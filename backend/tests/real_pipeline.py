"""One-off script: run the real ingestion pipeline against test-policies/*.pdf
using the real model and the live MCP tool server.

Category generation, extraction, grounding validation, and the writes to
app/db/documents/ and app/db/policies.json all go through the real code path.
Tool names and parameters come from fetch_tool_manifest(), which calls
tools/list on MCP_SERVER_URL on every run.

Run from the repo root: python -m backend.tests.real_pipeline
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ingestion import extraction, pipeline

TEST_POLICIES_DIR = Path(__file__).resolve().parents[2] / "test-policies"


async def main() -> None:
    tool_manifest = await extraction.fetch_tool_manifest()
    print(f"MCP tools: {[t['name'] for t in tool_manifest]}\n")

    pdfs = sorted(TEST_POLICIES_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} document(s): {[p.name for p in pdfs]}\n")

    print("--- Running the real pipeline (process_documents) ---")
    start = time.perf_counter()
    results = await pipeline.process_documents(pdfs)
    elapsed = time.perf_counter() - start
    flagged = sum(1 for r in results if r["needs_review"])
    print(f"Done in {elapsed:.1f}s -> {len(results)} rule(s), {flagged} flagged for review")
    print(
        f"Written to {pipeline.DOCUMENTS_DIR}, {pipeline.CATEGORIES_PATH}, "
        f"and {pipeline.POLICIES_PATH}\n"
    )

    print("--- Benchmark: concurrent vs. serial extraction ---")
    texts = [pipeline.extract_text(p) for p in pdfs]
    categories = await pipeline.get_or_generate_categories(tool_manifest, texts[0])

    start = time.perf_counter()
    await asyncio.gather(
        *(extraction.extract_rules_from_text(t, tool_manifest, categories) for t in texts)
    )
    concurrent_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for t in texts:
        await extraction.extract_rules_from_text(t, tool_manifest, categories)
    serial_elapsed = time.perf_counter() - start

    print(
        f"Concurrent: {concurrent_elapsed:.1f}s | Serial: {serial_elapsed:.1f}s "
        f"| Speedup: {serial_elapsed / concurrent_elapsed:.2f}x"
    )


if __name__ == "__main__":
    asyncio.run(main())
