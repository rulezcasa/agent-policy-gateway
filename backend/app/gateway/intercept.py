"""One intercept: rewrite, compare, explain conflicts, then forward or hold."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from .. import services
from ..policy_engine.evaluator import evaluate
from ..policy_engine.explain import explain
from ..policy_engine.normalize import normalize
from ..policy_engine.store import (
    append_action,
    append_pending,
    read_policies,
    read_workflow_state,
)
from .forward import forward_tool

OWNERSHIP_POLICY_ID = "order_must_belong_to_caller"
OWNERSHIP_CUSTOMER_MESSAGE = "This isn't the phone number associated with the account."


async def intercept(tool: str, arguments: dict) -> str:
    created_at = datetime.now(timezone.utc).isoformat()
    action_id = f"act_{uuid.uuid4().hex[:8]}"
    raw = {key: value for key, value in arguments.items() if value is not None}
    workflow = read_workflow_state()
    agent_id = workflow.get("active_agent") or "ai_agent"
    actor_role = "ai_agent"

    order_context = _order_context(raw, workflow.get("phone"))
    normalized = await normalize(tool, raw, order_context)
    for key in ("order_customer_id", "caller_customer_id", "order_owner_mismatch", "days_since_ordered_on"):
        if key in order_context and order_context[key] is not None:
            normalized["arguments"][key] = order_context[key]
    verdict = evaluate(
        {"action": normalized["action"], "arguments": normalized["arguments"]},
        read_policies(),
        actor_role=actor_role,
    )
    reasoning = None
    customer_message = None
    winner = verdict.get("policy")
    if verdict["decision"] != "allow":
        if _is_ownership_policy(winner):
            customer_message = OWNERSHIP_CUSTOMER_MESSAGE
            reasoning = customer_message
        else:
            reasoning = await explain(verdict["policy"], normalized["arguments"], verdict["decision"])

    record = {
        "action_id": action_id,
        "agent_id": agent_id,
        "actor_role": actor_role,
        "tool": tool,
        "action": normalized["action"],
        "arguments": raw,
        "normalized_arguments": normalized["arguments"],
        "timestamp": created_at,
        "decision": verdict["decision"],
        "policy_ids": verdict["policy_ids"],
        "required_approval": verdict["required_approval"],
        "llm_reasoning": reasoning,
        "customer_message": customer_message,
    }
    append_action(record)

    if verdict["decision"] == "allow":
        result = await forward_tool(tool, raw)
        return (
            f"GATEWAY ALLOWED action_id={action_id}. "
            "The policy check allowed this call. Tell the customer it went through.\n"
            f"{result}"
        )

    task = {
        **record,
        "status": "pending_approval" if verdict["decision"] == "requires_approval" else "blocked",
        "workflow_state": workflow,
        "tool_result": None,
        "resolution": None,
        "created_at": created_at,
    }
    append_pending(task)
    return _agent_message(task)


def _order_context(arguments: dict, phone: str | None) -> dict:
    order_id = arguments.get("order_id")
    if not order_id:
        return {}
    try:
        order = services.get_order(str(order_id))
    except services.NotFoundError:
        return {}
    data = order.model_dump()
    ordered_on = data.get("ordered_on")
    ordered_on_value = ordered_on.isoformat() if hasattr(ordered_on, "isoformat") else ordered_on
    order_customer_id = data.get("customer_id")
    caller_customer_id = _caller_customer_id(phone)
    return {
        "fulfillment_status": data.get("fulfillment_status"),
        "payment_method": data.get("payment_method"),
        "ordered_on": ordered_on_value,
        "days_since_ordered_on": _days_since(ordered_on_value),
        "amount": data.get("amount"),
        "currency": data.get("currency"),
        "customer_id": order_customer_id,
        "order_customer_id": order_customer_id,
        "caller_customer_id": caller_customer_id,
        "order_owner_mismatch": caller_customer_id is None or order_customer_id != caller_customer_id,
    }


def _days_since(ordered_on: str | None) -> int | None:
    if not ordered_on:
        return None
    try:
        ordered = date.fromisoformat(str(ordered_on)[:10])
    except ValueError:
        return None
    return (date.today() - ordered).days


def _caller_customer_id(phone: str | None) -> str | None:
    if not phone:
        return None
    try:
        return services.get_customer(str(phone)).customer_id
    except services.NotFoundError:
        return None


def _is_ownership_policy(policy: dict | None) -> bool:
    if not policy:
        return False
    if policy.get("policy_id") == OWNERSHIP_POLICY_ID:
        return True
    return any(
        condition.get("field") == "order_owner_mismatch" and condition.get("value") is True
        for condition in policy.get("conditions") or []
    )


def _agent_message(task: dict) -> str:
    reasoning = task.get("llm_reasoning") or "A company policy applies to this request."
    if task["decision"] == "requires_approval":
        role = task.get("required_approval") or "a manager"
        return (
            f"HELD action_id={task['action_id']}. "
            f"This request needs approval from {role}. {reasoning} "
            "Do not retry this tool."
        )
    return (
        f"BLOCKED action_id={task['action_id']}. {reasoning} "
        "Tell the customer exactly: "
        f"{task.get('customer_message') or reasoning} "
        "Do not retry this tool."
    )
