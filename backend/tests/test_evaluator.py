"""Rule engine cases. No model and no MCP."""

from app.policy_engine.evaluator import evaluate


def _policy(
    policy_id,
    action,
    decision,
    conditions=None,
    roles=None,
    priority=0,
    status="active",
    approval_role=None,
):
    return {
        "policy_id": policy_id,
        "action": action,
        "decision": decision,
        "conditions": conditions or [],
        "subject": {"roles": roles if roles is not None else ["ai_assistant"]},
        "priority": priority,
        "status": status,
        "approval_role": approval_role,
    }


REFUND_100 = _policy(
    "refund_100",
    "issue_refund",
    "requires_approval",
    conditions=[{"field": "amount", "operator": ">", "value": 100}],
    priority=50,
    approval_role="manager",
)
REFUND_500 = _policy(
    "refund_500",
    "issue_refund",
    "requires_approval",
    conditions=[{"field": "amount", "operator": ">", "value": 500}],
    priority=90,
    approval_role="finance_director",
)
DISCOUNT = _policy(
    "discount_cap",
    "apply_discount",
    "block",
    conditions=[{"field": "discount_percent", "operator": ">", "value": 20}],
)
CREDIT = _policy("credit_block", "get_credit_application", "block")
EXPORT = _policy("export_block", "export_customer_list", "block")


def test_refund_under_limit_allows():
    verdict = evaluate({"action": "issue_refund", "arguments": {"amount": 80}}, [REFUND_100, REFUND_500])
    assert verdict["decision"] == "allow"
    assert verdict["policy_ids"] == []


def test_refund_over_100_needs_manager():
    verdict = evaluate({"action": "issue_refund", "arguments": {"amount": 150}}, [REFUND_100, REFUND_500])
    assert verdict["decision"] == "requires_approval"
    assert verdict["required_approval"] == "manager"
    assert verdict["policy_ids"] == ["refund_100"]


def test_refund_over_500_uses_higher_priority():
    verdict = evaluate({"action": "issue_refund", "arguments": {"amount": 600}}, [REFUND_100, REFUND_500])
    assert verdict["decision"] == "requires_approval"
    assert verdict["required_approval"] == "finance_director"
    assert verdict["policy_ids"][0] == "refund_500"


def test_discount_over_cap_blocks():
    verdict = evaluate({"action": "apply_discount", "arguments": {"discount_percent": 25}}, [DISCOUNT])
    assert verdict["decision"] == "block"


def test_empty_conditions_block_credit_and_export():
    assert evaluate({"action": "get_credit_application", "arguments": {}}, [CREDIT])["decision"] == "block"
    assert evaluate({"action": "export_customer_list", "arguments": {}}, [EXPORT])["decision"] == "block"


def test_pending_review_is_ignored():
    draft = _policy(
        "draft",
        "issue_refund",
        "block",
        conditions=[{"field": "amount", "operator": ">", "value": 1}],
        status="pending_review",
    )
    verdict = evaluate({"action": "issue_refund", "arguments": {"amount": 150}}, [draft])
    assert verdict["decision"] == "allow"


def test_role_mismatch_is_ignored():
    human_only = _policy(
        "desk",
        "issue_refund",
        "block",
        conditions=[{"field": "amount", "operator": ">", "value": 1}],
        roles=["support_desk"],
    )
    verdict = evaluate(
        {"action": "issue_refund", "arguments": {"amount": 150}},
        [human_only],
        actor_role="ai_agent",
    )
    assert verdict["decision"] == "allow"


def test_order_owner_mismatch_blocks_ahead_of_refund_approval():
    ownership = _policy(
        "order_owner",
        "*",
        "block",
        conditions=[{"field": "order_owner_mismatch", "operator": "==", "value": True}],
        priority=100,
    )
    verdict = evaluate(
        {"action": "issue_refund", "arguments": {"amount": 600, "order_owner_mismatch": True}},
        [REFUND_100, REFUND_500, ownership],
    )
    assert verdict["decision"] == "block"
    assert verdict["policy_ids"][0] == "order_owner"
    assert verdict["required_approval"] is None


def test_matching_owner_still_uses_refund_rule():
    ownership = _policy(
        "order_owner",
        "*",
        "block",
        conditions=[{"field": "order_owner_mismatch", "operator": "==", "value": True}],
        priority=100,
    )
    verdict = evaluate(
        {"action": "issue_refund", "arguments": {"amount": 150, "order_owner_mismatch": False}},
        [REFUND_100, ownership],
    )
    assert verdict["decision"] == "requires_approval"
    assert verdict["required_approval"] == "manager"


def test_alias_matches_ai_assistant_label():
    verdict = evaluate(
        {"action": "issue_refund", "arguments": {"amount": 150}},
        [REFUND_100],
        actor_role="ai_agent",
    )
    assert verdict["decision"] == "requires_approval"
