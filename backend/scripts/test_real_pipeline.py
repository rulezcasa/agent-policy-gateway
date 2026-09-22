"""One-off script: run the real ingestion pipeline against test-policies/*.pdf
using the real model on the ZGX Nano.

Only fetch_tool_manifest is faked out (with the real Maplewood tool list),
since no MCP server is running locally yet — everything else (category
generation, extraction, grounding validation, writing documents.json /
policies.json) is the real code path, hitting the real model.

Also times concurrent vs. serial extraction to confirm the parallel design
is actually faster, not just structured that way.

Run from backend/: python -m scripts.test_real_pipeline
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from app.ingestion import llm_client, pipeline

TEST_POLICIES_DIR = Path(__file__).resolve().parents[2] / "test-policies"

# Real Maplewood tools (from mcp_server.py) — faked here only because no MCP
# server is reachable yet from this machine.
FAKE_TOOL_MANIFEST = [
    {
        "name": "get_customer_record",
        "description": "Look up a customer by the phone they're chatting from. GET /customers.",
        "parameters": {"properties": {"phone": {}}},
    },
    {
        "name": "get_order_status",
        "description": "Get order details. GET /orders/{order_id}.",
        "parameters": {"properties": {"order_id": {}}},
    },
    {
        "name": "get_orders",
        "description": "List every order for a customer. GET /customers/{customer_id}/orders.",
        "parameters": {"properties": {"customer_id": {}}},
    },
    {
        "name": "issue_refund",
        "description": "Issue a refund. POST /orders/{order_id}/refunds.",
        "parameters": {
            "properties": {
                "order_id": {},
                "customer_id": {},
                "amount": {},
                "reason": {},
                "payment_method": {},
                "currency": {},
            }
        },
    },
    {
        "name": "apply_discount",
        "description": "Apply a percent discount. POST /orders/{order_id}/discounts.",
        "parameters": {"properties": {"order_id": {}, "discount_percent": {}, "reason": {}}},
    },
    {
        "name": "get_credit_application",
        "description": "Fetch a credit-account application. GET /customers/{id}/credit-application.",
        "parameters": {"properties": {"customer_id": {}}},
    },
    {
        "name": "export_customer_list",
        "description": "Export every customer record. POST /customers/export.",
        "parameters": {"properties": {"destination": {}, "reason": {}}},
    },
    {
        "name": "update_shipping_address",
        "description": "Replace the shipping address. PUT /orders/{order_id}/shipping-address.",
        "parameters": {
            "properties": {
                "order_id": {},
                "street": {},
                "city": {},
                "state": {},
                "postal_code": {},
                "country": {},
            }
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an order. POST /orders/{order_id}/cancel.",
        "parameters": {"properties": {"order_id": {}, "reason": {}}},
    },
    {
        "name": "return_order",
        "description": (
            "Return a delivered order within 10 days of ordered_on and refund "
            "its full amount. POST /orders/{order_id}/return."
        ),
        "parameters": {"properties": {"order_id": {}, "reason": {}}},
    },
]


async def _fake_fetch_tool_manifest(*args, **kwargs):
    return FAKE_TOOL_MANIFEST


async def main() -> None:
    llm_client.fetch_tool_manifest = _fake_fetch_tool_manifest

    pdfs = sorted(TEST_POLICIES_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} document(s): {[p.name for p in pdfs]}\n")

    print("--- Running the real pipeline (process_documents) ---")
    start = time.perf_counter()
    results = await pipeline.process_documents(pdfs)
    elapsed = time.perf_counter() - start
    flagged = sum(1 for r in results if r["needs_review"])
    print(f"Done in {elapsed:.1f}s -> {len(results)} rule(s), {flagged} flagged for review")
    print(f"Written to {pipeline.DOCUMENTS_PATH} and {pipeline.POLICIES_PATH}\n")
    print(json.dumps(results, indent=2))

    print("\n--- Benchmark: concurrent vs. serial extraction ---")
    texts = [pipeline.extract_text(p) for p in pdfs]
    categories = await llm_client.get_or_generate_categories(FAKE_TOOL_MANIFEST, texts[0])

    start = time.perf_counter()
    await asyncio.gather(
        *(llm_client.extract_rules_from_text(t, FAKE_TOOL_MANIFEST, categories) for t in texts)
    )
    concurrent_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for t in texts:
        await llm_client.extract_rules_from_text(t, FAKE_TOOL_MANIFEST, categories)
    serial_elapsed = time.perf_counter() - start

    print(
        f"Concurrent: {concurrent_elapsed:.1f}s | Serial: {serial_elapsed:.1f}s "
        f"| Speedup: {serial_elapsed / concurrent_elapsed:.2f}x"
    )


if __name__ == "__main__":
    asyncio.run(main())
