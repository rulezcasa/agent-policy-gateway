import pytest
from mcp import Client

from app.tools import data
from app.tools.server import mcp

EXPECTED_TOOLS = {
    "get_customer_record",
    "get_order_status",
    "update_shipping_address",
    "cancel_order",
    "issue_refund",
    "apply_discount",
    "get_credit_application",
    "export_customer_list",
}


@pytest.fixture(autouse=True)
def reset_data() -> None:
    data.reset()


@pytest.mark.anyio
async def test_lists_maplewood_tools() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {tool.name for tool in tools.tools}
    assert names == EXPECTED_TOOLS


@pytest.mark.anyio
async def test_get_customer_by_phone() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("get_customer_record", {"phone": "555-0198"})

    assert result.structured_content["customer_id"] == "cust_201"
    assert result.structured_content["name"] == "Elena Vasquez"
    assert result.structured_content["order_ids"] == ["ORD-1488"]


@pytest.mark.anyio
async def test_get_order_matches_api_shape() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("get_order_status", {"order_id": "ORD-1704"})

    body = result.structured_content
    assert body["product"] == "Oak dining chairs (set of 2)"
    assert body["fulfillment_status"] == "processing"
    assert body["shipping_address"]["street"] == "12 Pine Rd"


@pytest.mark.anyio
async def test_issue_refund_matches_api_shape() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "issue_refund",
            {
                "customer_id": "cust_201",
                "order_id": "ORD-1488",
                "amount": 80.0,
                "reason": "returned lamp",
            },
        )

    body = result.structured_content
    assert body["ok"] is True
    assert body["refund_id"].startswith("ref_1488_")
    assert body["amount"] == 80.0
    assert body["payment_method"] == "card"


@pytest.mark.anyio
async def test_apply_discount_returns_new_total() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "apply_discount",
            {"order_id": "ORD-1488", "discount_percent": 25, "reason": "sorry discount"},
        )

    assert result.structured_content["amount"] == 60.0


@pytest.mark.anyio
async def test_update_address_and_cancel() -> None:
    async with Client(mcp) as client:
        updated = await client.call_tool(
            "update_shipping_address",
            {
                "order_id": "ORD-1704",
                "street": "88 Harbor St",
                "city": "Portland",
                "state": "OR",
                "postal_code": "97201",
            },
        )
        cancelled = await client.call_tool(
            "cancel_order",
            {"order_id": "ORD-1690", "reason": "customer changed mind"},
        )

    assert updated.structured_content["shipping_address"]["street"] == "88 Harbor St"
    assert cancelled.structured_content["fulfillment_status"] == "cancelled"
