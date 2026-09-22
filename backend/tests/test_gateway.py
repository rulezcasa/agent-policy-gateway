from fastapi.testclient import TestClient

from app.data import ORDERS
from app.main import app


client = TestClient(app)


def check(agent_id: str, tool: str, arguments: dict) -> dict:
    response = client.post(
        "/gateway/check",
        json={
            "agent_id": agent_id,
            "actor_role": "ai_agent",
            "tool": tool,
            "arguments": arguments,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_demo_decisions_cover_new_use_case() -> None:
    ORDERS["ORD-1690"].fulfillment_status = "dispatched"

    assert check(
        "refund_agent", "issue_refund", {"amount": 80, "payment_method": "card"}
    )["decision"]["decision"] == "allow"

    manager = check(
        "refund_agent", "issue_refund", {"amount": 150, "payment_method": "card"}
    )["decision"]
    assert manager["decision"] == "requires_approval"
    assert manager["required_approval"] == "manager"

    assert check(
        "refund_agent", "issue_refund", {"amount": 50, "payment_method": "gift_card"}
    )["decision"]["decision"] == "block"

    assert check(
        "refund_agent", "apply_discount", {"discount_percent": 25}
    )["decision"]["decision"] == "block"

    assert check(
        "support_agent", "get_credit_application", {"customer_id": "cust_193"}
    )["decision"]["decision"] == "block"

    assert check(
        "support_agent", "export_customer_list", {"destination": "partner_campaign"}
    )["decision"]["decision"] == "block"

    assert check(
        "order_agent",
        "update_shipping_address",
        {"order_id": "ORD-1704"},
    )["decision"]["decision"] == "allow"

    assert check(
        "order_agent",
        "cancel_order",
        {"order_id": "ORD-1690"},
    )["decision"]["decision"] == "block"

    finance = check(
        "refund_agent", "issue_refund", {"amount": 600, "payment_method": "card"}
    )["decision"]
    assert finance["decision"] == "requires_approval"
    assert finance["required_approval"] == "finance_director"


def test_approval_queue_can_resolve_manager_request() -> None:
    result = check(
        "refund_agent", "issue_refund", {"amount": 150, "payment_method": "card"}
    )
    action_id = result["action"]["action_id"]

    pending = client.get("/gateway/approvals")
    assert pending.status_code == 200
    assert any(item["action"]["action_id"] == action_id for item in pending.json())

    resolved = client.post(
        f"/gateway/approvals/{action_id}",
        json={"by": "manager_priya", "outcome": "approved"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["decision"]["resolution"]["outcome"] == "approved"
