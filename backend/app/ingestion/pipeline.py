"""Turns uploaded policy PDFs into validated entries under backend/app/db/.

Text/table extraction runs in parallel across documents (CPU-only, no GPU).
LLM extraction also runs concurrently across documents, but every request
goes to the same Ollama model the agents use (qwen3.6-35b-q8-tools).
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

from . import extraction

DB_DIR = Path(__file__).resolve().parents[1] / "db"
POLICIES_PATH = DB_DIR / "policies.json"
CATEGORIES_PATH = DB_DIR / "categories.json"
DOCUMENTS_DIR = DB_DIR / "documents"

# Where an upload endpoint saves incoming files before processing them —
# process_documents() only ever deals in paths that already exist on disk.
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Fields the gateway enriches onto an action's arguments at enforcement time
# (see API_CONTRACTS.md) — valid condition targets even though they're not
# arguments of the tool call itself.
ENRICHMENT_FIELDS = {
    "fulfillment_status",
    "payment_method",
    "ordered_on",
    "amount",
    "currency",
    "order_customer_id",
    "caller_customer_id",
    "order_owner_mismatch",
    "days_since_ordered_on",
}
WILDCARD_ACTION = "*"
_STATUS_VALUE_FIELDS = {
    "orders_with_status_processing": ("==", "processing"),
    "orders_with_status_dispatched": ("==", "dispatched"),
    "orders_with_status_dispatched_or_delivered": ("in", ["dispatched", "delivered"]),
}
_OWNERSHIP_MARKERS = (
    "act only on an order",
    "order that belongs",
    "order belonging to someone else",
    "not on that customer's account",
    "orders_not_owned_by_current_customer",
)


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


def canonicalize_rule(rule: dict) -> dict:
    """Rewrite extracted rules into fields the evaluator compares.

    The model often emits a role, a single tool, or a made-up set name for a
    sentence the gateway already represents as order_owner_mismatch or
    fulfillment_status. Those rules never match, so the call is allowed.
    """
    updated = dict(rule)
    conditions = [_canonicalize_condition(item) for item in rule.get("conditions") or []]
    updated["conditions"] = conditions
    text = f"{rule.get('name', '')}\n{rule.get('original_text', '')}".lower()
    for condition in rule.get("conditions") or []:
        if condition.get("value") == "orders_not_owned_by_current_customer":
            text += "\norders_not_owned_by_current_customer"

    if any(marker in text for marker in _OWNERSHIP_MARKERS):
        updated["action"] = WILDCARD_ACTION
        updated["decision"] = "block"
        updated["conditions"] = [
            {"field": "order_owner_mismatch", "operator": "==", "value": True}
        ]
        updated["priority"] = 100
    elif (
        updated.get("decision") == "block"
        and not updated["conditions"]
        and "no exceptions" in text
    ):
        # "No exceptions to the table" is not a second rule that blocks every refund.
        updated["decision"] = "allow"

    updated["subject_roles"] = ["ai_agent"]
    return updated


def _roles(rule: dict) -> list:
    if rule.get("subject_roles") is not None:
        return list(rule["subject_roles"])
    return list((rule.get("subject") or {}).get("roles") or [])


_STATUS_WORDS = {
    "processing": "processing",
    "dispatched": "dispatched",
    "delivered": "delivered",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def _canonicalize_condition(condition: dict) -> dict:
    value = condition.get("value")
    if isinstance(value, str) and value in _STATUS_VALUE_FIELDS:
        operator, rewritten = _STATUS_VALUE_FIELDS[value]
        return {"field": "fulfillment_status", "operator": operator, "value": rewritten}
    updated = dict(condition)
    if updated.get("field") == "order_status":
        updated["field"] = "fulfillment_status"
    if updated.get("field") == "fulfillment_status" and isinstance(updated.get("value"), str):
        updated["value"] = _STATUS_WORDS.get(updated["value"].strip().lower(), updated["value"])
    return updated


def _validate_rule(rule: dict, tool_manifest: list[dict]) -> tuple[dict, bool]:
    """Grounds action + conditions[].field against the real tool manifest.

    This is the safety net for anything guided-JSON decoding didn't fully
    enforce: a rule that fails grounding is still saved, just flagged, so a
    human catches it on /policies/review instead of it silently never firing.
    """
    action = rule.get("action")
    if action == WILDCARD_ACTION:
        parameter_names = set().union(
            *(tool["parameters"].get("properties", {}) for tool in tool_manifest)
        ) if tool_manifest else set()
        valid_fields = ENRICHMENT_FIELDS | parameter_names
        needs_review = False
    else:
        tool = next((item for item in tool_manifest if item["name"] == action), None)
        needs_review = tool is None
        valid_fields = ENRICHMENT_FIELDS | set(
            tool["parameters"].get("properties", {}) if tool else {}
        )
    for condition in rule.get("conditions", []):
        if condition.get("field") not in valid_fields:
            needs_review = True
        if condition.get("operator") not in extraction.CONDITION_OPERATORS:
            needs_review = True

    return rule, needs_review


def rule_needs_review(action: str, conditions: list[dict], tool_manifest: list[dict]) -> bool:
    """True when the action or its condition fields are not grounded on a live tool."""
    _, needs_review = _validate_rule({"action": action, "conditions": conditions}, tool_manifest)
    return needs_review


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
        "priority": rule.get("priority") or 0,
        "version": 1,
        "status": "pending_review",
        "source_doc": doc_id,
        "original_text": rule["original_text"],
        "needs_review": needs_review,
    }


def list_documents() -> list[dict]:
    if not DOCUMENTS_DIR.exists():
        return []
    return [json.loads(path.read_text()) for path in sorted(DOCUMENTS_DIR.glob("*.json"))]


def _write_documents(records: list[dict]) -> None:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = DOCUMENTS_DIR / f"{record['doc_id']}.json"
        path.write_text(json.dumps(record, indent=2))


def clear_policy_data() -> dict:
    """Drop extracted rules, taxonomy, document records, and uploaded PDFs."""
    policies = load_policies()
    documents = list_documents()
    uploads = [path for path in UPLOADS_DIR.iterdir() if path.is_file()] if UPLOADS_DIR.exists() else []
    POLICIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICIES_PATH.write_text("[]\n")
    if CATEGORIES_PATH.exists():
        CATEGORIES_PATH.unlink()
    for path in DOCUMENTS_DIR.glob("*.json") if DOCUMENTS_DIR.exists() else []:
        path.unlink()
    for path in uploads:
        path.unlink()
    return {
        "policies_removed": len(policies),
        "documents_removed": len(documents),
        "uploads_removed": len(uploads),
    }


def load_policies() -> list[dict]:
    """Rules in policies.json. A missing or blank file means there are none."""
    if not POLICIES_PATH.exists():
        return []
    raw = POLICIES_PATH.read_text().strip()
    if not raw:
        return []
    data = json.loads(raw)
    return data if isinstance(data, list) else []


def load_categories() -> list[dict] | None:
    if not CATEGORIES_PATH.exists():
        return None
    raw = CATEGORIES_PATH.read_text().strip()
    if not raw:
        return None
    return json.loads(raw)


def save_categories(categories: list[dict]) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    CATEGORIES_PATH.write_text(json.dumps(categories, indent=2))


async def get_or_generate_categories(
    tool_manifest: list[dict], sample_text: str, *, force_refresh: bool = False
) -> list[dict]:
    """Reuse the tenant taxonomy in app/db/categories.json, or generate it
    once and write it there. One taxonomy per tenant, not one per document.
    """
    if not force_refresh:
        cached = load_categories()
        if cached is not None:
            return cached

    categories = await extraction.generate_categories(tool_manifest, sample_text)
    save_categories(categories)
    return categories


def _append_json(path: Path, records: list[dict]) -> None:
    raw = path.read_text().strip() if path.exists() else ""
    existing = json.loads(raw) if raw else []
    if not isinstance(existing, list):
        existing = []
    existing.extend(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2))


def update_policy(policy_id: str, updates: dict) -> dict:
    """Applies a reviewer's decision (confirm/edit/reject) to one policy.

    `updates` may set "status" (pending_review -> active or draft) and/or
    edit any structured field. Editing anything other than status bumps
    "version", per DATA_MODELS.md.
    """
    policies = load_policies()
    for policy in policies:
        if policy["policy_id"] == policy_id:
            if any(field != "status" for field in updates):
                policy["version"] += 1
            policy.update(updates)
            POLICIES_PATH.write_text(json.dumps(policies, indent=2))
            return policy
    raise KeyError(f"Unknown policy_id: {policy_id}")


async def process_documents(file_paths: list[Path]) -> list[dict]:
    """Entrypoint: PDFs in, validated policy rule dicts out (also written
    to app/db/documents/, app/db/categories.json, and app/db/policies.json).
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
    _write_documents(doc_records)

    tool_manifest = await extraction.fetch_tool_manifest()
    sample_text = next(iter(texts_by_path.values()), "")
    categories = await get_or_generate_categories(tool_manifest, sample_text)

    raw_rule_lists = await asyncio.gather(
        *(
            extraction.extract_rules_from_text(texts_by_path[path], tool_manifest, categories)
            for path in file_paths
        )
    )

    policies: list[dict] = []
    for path, raw_rules in zip(file_paths, raw_rule_lists):
        for rule in raw_rules:
            rule = canonicalize_rule(rule)
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
    print(
        f"Extracted {len(results)} rule(s) -> {POLICIES_PATH} "
        f"({flagged} flagged for review); categories -> {CATEGORIES_PATH}"
    )
