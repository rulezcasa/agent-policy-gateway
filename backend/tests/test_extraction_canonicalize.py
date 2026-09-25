"""Extraction rewrite for rules the model emits in a shape the engine cannot match."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ingestion.pipeline import canonicalize_rule
from app.policy_engine.evaluator import evaluate


def test_ownership_sentence_becomes_a_mismatch_block():
    rule = canonicalize_rule(
        {
            "name": "Order ownership validation",
            "subject_roles": ["customer"],
            "action": "get_order_status",
            "conditions": [
                {
                    "field": "order_id",
                    "operator": "in",
                    "value": "orders_not_owned_by_current_customer",
                }
            ],
            "decision": "block",
            "original_text": (
                "Staff may act only on an order that belongs to the customer "
                "associated with the phone number."
            ),
        }
    )
    assert rule["action"] == "*"
    assert rule["subject_roles"] == ["ai_agent"]
    assert rule["conditions"] == [
        {"field": "order_owner_mismatch", "operator": "==", "value": True}
    ]
    assert rule["priority"] == 100

    policy = {
        "policy_id": "order_owner",
        "action": rule["action"],
        "decision": rule["decision"],
        "conditions": rule["conditions"],
        "subject": {"roles": rule["subject_roles"]},
        "priority": rule["priority"],
        "status": "active",
    }
    verdict = evaluate(
        {
            "action": "issue_refund",
            "arguments": {"amount": 150, "order_owner_mismatch": True},
        },
        [policy],
        actor_role="ai_agent",
    )
    assert verdict["decision"] == "block"


def test_status_set_name_becomes_fulfillment_status():
    rule = canonicalize_rule(
        {
            "name": "Cancel order after dispatch prohibited",
            "subject_roles": ["customer"],
            "action": "cancel_order",
            "conditions": [
                {
                    "field": "order_id",
                    "operator": "in",
                    "value": "orders_with_status_dispatched_or_delivered",
                }
            ],
            "decision": "block",
            "original_text": "Once the status is Dispatched, the order cannot be cancelled.",
        }
    )
    assert rule["subject_roles"] == ["ai_agent"]
    assert rule["conditions"] == [
        {"field": "fulfillment_status", "operator": "in", "value": ["dispatched", "delivered"]}
    ]
