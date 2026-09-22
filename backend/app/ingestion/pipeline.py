"""Turns uploaded policy PDFs into validated entries in documents.json and
policies.json.

Text/table extraction runs in parallel across documents (CPU-only, no GPU).
LLM extraction also runs concurrently across documents, but every request
goes to the same single model instance on the ZGX Nano — vLLM's continuous
batching handles the actual parallelism server-side, so this never spins up
more than one model.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

from . import llm_client

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DOCUMENTS_PATH = DATA_DIR / "documents.json"
POLICIES_PATH = DATA_DIR / "policies.json"

# Fields the gateway enriches onto an action's arguments at enforcement time
# (see API_CONTRACTS.md) — valid condition targets even though they're not
# arguments of the tool call itself.
ENRICHMENT_FIELDS = {"fulfillment_status", "payment_method"}


def extract_text(pdf_path: Path) -> str:
    """Plain text + tables (rendered as Markdown) from one PDF, page by page.

    Text-only extraction — no OCR/vision fallback. Fine for the documents
    this gateway ingests today; revisit if a client's real documents turn
    out to be scanned/image-only.
    """
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
            for table in page.extract_tables():
                if table:
                    parts.append(_table_to_markdown(table))
    return "\n\n".join(parts)


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [[cell or "" for cell in row] for row in table]
    header, *body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


async def _extract_all_text(file_paths: list[Path]) -> dict[Path, str]:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=len(file_paths) or 1) as pool:
        texts = await asyncio.gather(
            *(loop.run_in_executor(pool, extract_text, path) for path in file_paths)
        )
    return dict(zip(file_paths, texts))


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "policy"


def _validate_rule(rule: dict, tool_manifest: list[dict]) -> tuple[dict, bool]:
    """Grounds action + conditions[].field against the real tool manifest.

    This is the safety net for anything guided-JSON decoding didn't fully
    enforce: a rule that fails grounding is still saved, just flagged, so a
    human catches it on /policies/review instead of it silently never firing.
    """
    tool = next((t for t in tool_manifest if t["name"] == rule.get("action")), None)
    needs_review = tool is None

    valid_fields = ENRICHMENT_FIELDS | set(
        tool["parameters"].get("properties", {}) if tool else {}
    )
    for condition in rule.get("conditions", []):
        if condition.get("field") not in valid_fields:
            needs_review = True
        if condition.get("operator") not in llm_client.CONDITION_OPERATORS:
            needs_review = True

    return rule, needs_review


def _build_policy(rule: dict, doc_id: str, needs_review: bool) -> dict:
    return {
        "policy_id": f"{_slugify(rule['name'])}_{uuid.uuid4().hex[:6]}",
        "name": rule["name"],
        "category": rule["category"],
        "subject": {"roles": rule["subject_roles"]},
        "action": rule["action"],
        "conditions": rule["conditions"],
        "decision": rule["decision"],
        "approval_role": rule.get("approval_role"),
        "priority": rule["priority"],
        "version": 1,
        "status": "pending_review",
        "source_doc": doc_id,
        "original_text": rule["original_text"],
        "needs_review": needs_review,
    }


def _append_json(path: Path, records: list[dict]) -> None:
    existing = json.loads(path.read_text()) if path.exists() else []
    existing.extend(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2))


async def process_documents(file_paths: list[Path]) -> list[dict]:
    """Entrypoint: PDFs in, validated policy rule dicts out (also appended
    to documents.json / policies.json). This is the function an upload
    endpoint would call once one exists.
    """
    texts_by_path = await _extract_all_text(file_paths)

    doc_ids: dict[Path, str] = {path: f"doc_{uuid.uuid4().hex[:8]}" for path in file_paths}
    doc_records = [
        {
            "doc_id": doc_ids[path],
            "filename": path.name,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "raw_text": texts_by_path[path],
            "status": "extracted",
        }
        for path in file_paths
    ]
    _append_json(DOCUMENTS_PATH, doc_records)

    tool_manifest = await llm_client.fetch_tool_manifest()
    sample_text = next(iter(texts_by_path.values()), "")
    categories = await llm_client.get_or_generate_categories(tool_manifest, sample_text)

    raw_rule_lists = await asyncio.gather(
        *(
            llm_client.extract_rules_from_text(texts_by_path[path], tool_manifest, categories)
            for path in file_paths
        )
    )

    policies: list[dict] = []
    for path, raw_rules in zip(file_paths, raw_rule_lists):
        for rule in raw_rules:
            rule, needs_review = _validate_rule(rule, tool_manifest)
            policies.append(_build_policy(rule, doc_ids[path], needs_review))

    _append_json(POLICIES_PATH, policies)
    return policies


if __name__ == "__main__":
    import sys

    repo_root = Path(__file__).resolve().parents[3]
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        paths = sorted((repo_root / "test-policies").glob("*.pdf"))

    if not paths:
        raise SystemExit("No PDFs given and none found in test-policies/")

    print(f"Processing {len(paths)} document(s)...")
    results = asyncio.run(process_documents(paths))
    flagged = sum(1 for r in results if r["needs_review"])
    print(f"Extracted {len(results)} rule(s) -> {POLICIES_PATH} ({flagged} flagged for review)")
