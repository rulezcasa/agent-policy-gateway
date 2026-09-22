from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from ..data import ORDERS
from ..models.gateway_models import AgentAction, ActionRequest, GatewayDecision, GatewayResult, Policy
from ..policies import POLICIES


def _condition_matches(condition: Any, arguments: dict[str, Any]) -> bool:
    actual = arguments.get(condition.field)
    expected = condition.value
    if actual is None:
        return False
    if condition.operator == "==":
        return actual == expected
    if condition.operator == "!=":
        return actual != expected
    if condition.operator == ">":
        return actual > expected
    if condition.operator == ">=":
        return actual >= expected
    if condition.operator == "<":
        return actual < expected
    if condition.operator == "<=":
        return actual <= expected
    if condition.operator == "in":
        return actual in expected
    return False


def _arguments_with_order_context(action: ActionRequest) -> dict[str, Any]:
    arguments = dict(action.arguments)
    order_id = arguments.get("order_id")
    order = ORDERS.get(order_id)
    if order is not None:
        arguments.setdefault("fulfillment_status", order.fulfillment_status)
        arguments.setdefault("payment_method", order.payment_method)
    return arguments


def _matching_policies(action: ActionRequest) -> list[Policy]:
    arguments = _arguments_with_order_context(action)
    semantic_action = action.action or action.tool
    matches = []
    for policy in POLICIES:
        if policy.status != "active" or policy.action != semantic_action:
            continue
        if action.actor_role not in policy.subject.roles:
            continue
        if all(_condition_matches(condition, arguments) for condition in policy.conditions):
            matches.append(policy)
    return sorted(matches, key=lambda policy: policy.priority, reverse=True)


def _reason(policy: Policy, action: ActionRequest) -> str:
    if policy.policy_id == "refund_gift_card_001":
        return "Gift card purchases cannot receive cash refunds; issue store credit instead."
    if policy.policy_id == "refund_finance_001":
        return "Refunds above $500 require finance director approval."
    if policy.policy_id == "refund_manager_001":
        return "Refunds above $100 require shift manager approval."
    if policy.policy_id == "discount_limit_001":
        return "Discounts larger than 20% are not permitted."
    if policy.policy_id == "credit_application_001":
        return "AI assistants must never access credit-account applications."
    if policy.policy_id == "customer_export_001":
        return "Customer lists must never be exported."
    if policy.policy_id == "shipping_update_status_001":
        return "Shipping addresses cannot be changed after courier handoff."
    if policy.policy_id == "order_cancel_status_001":
        return "Orders cannot be cancelled after courier handoff."
    return f"Action violates policy: {policy.name}."


def evaluate(action_request: ActionRequest) -> GatewayResult:
    action_id = f"act_{uuid4().hex[:8]}"
    action = AgentAction(
        action_id=action_id,
        agent_id=action_request.agent_id,
        actor_role=action_request.actor_role,
        tool=action_request.tool,
        action=action_request.action or action_request.tool,
        arguments=action_request.arguments,
        context=action_request.context,
        timestamp=datetime.now(timezone.utc),
    )
    matches = _matching_policies(action_request)
    winning_policy = matches[0] if matches else None
    if winning_policy is None:
        decision = "allow"
        reason = "No active policy blocked or required approval for this action."
        approval_role = None
        expires_at = None
    else:
        decision = winning_policy.decision
        reason = _reason(winning_policy, action_request)
        approval_role = winning_policy.approval_role
        expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=8)
            if decision == "requires_approval"
            else None
        )

    gateway_decision = GatewayDecision(
        decision=decision,
        action_id=action_id,
        policy_ids=[policy.policy_id for policy in matches[:1]],
        reason=reason,
        required_approval=approval_role,
        expires_at=expires_at,
        llm_reasoning=(
            f"{action.agent_id} attempted {action.action} with the supplied arguments."
        ),
    )
    return GatewayResult(action=action, decision=gateway_decision)
