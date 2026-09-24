"""Compare a normalized action to active policies. Rules are the only verdict."""

from __future__ import annotations

from typing import Any

DECISION_RANK = {"allow": 1, "requires_approval": 2, "block": 3}

ROLE_ALIASES = {
    "ai_agent": "ai_agent",
    "ai_assistant": "ai_agent",
    "ai assistant": "ai_agent",
    "automated_assistant": "ai_agent",
}


def evaluate(action: dict, policies: list[dict], actor_role: str = "ai_agent") -> dict:
    """Return the winning verdict for one normalized action.

    No matching rule means allow. Among matches, higher priority wins.
    Equal priority breaks toward block, then requires_approval, then allow.
    """
    action_name = action.get("action") or ""
    arguments = action.get("arguments") or {}
    triggered: list[dict] = []
    for policy in policies:
        if policy.get("status") != "active":
            continue
        if policy.get("action") not in (action_name, "*"):
            continue
        if not _role_matches(policy, actor_role):
            continue
        if _conditions_hold(policy.get("conditions") or [], arguments):
            triggered.append(policy)

    if not triggered:
        return {
            "decision": "allow",
            "policy_ids": [],
            "required_approval": None,
            "policy": None,
        }

    triggered.sort(key=_rank, reverse=True)
    winner = triggered[0]
    decision = winner.get("decision") or "allow"
    approval = winner.get("approval_role") if decision == "requires_approval" else None
    return {
        "decision": decision,
        "policy_ids": [policy.get("policy_id") for policy in triggered if policy.get("policy_id")],
        "required_approval": approval,
        "policy": winner,
    }


def _rank(policy: dict) -> tuple[int, int]:
    priority = policy.get("priority") or 0
    try:
        priority = int(priority)
    except (TypeError, ValueError):
        priority = 0
    return priority, DECISION_RANK.get(policy.get("decision") or "", 0)


def _role_matches(policy: dict, actor_role: str) -> bool:
    roles = (policy.get("subject") or {}).get("roles") or []
    if not roles:
        return True
    actor = _canonical_role(actor_role)
    return any(_canonical_role(role) == actor for role in roles)


def _canonical_role(role: str) -> str:
    key = " ".join(str(role).strip().lower().replace("-", " ").split())
    underscored = key.replace(" ", "_")
    return ROLE_ALIASES.get(key) or ROLE_ALIASES.get(underscored) or underscored


def _conditions_hold(conditions: list[dict], arguments: dict) -> bool:
    return all(_condition_holds(condition, arguments) for condition in conditions)


def _condition_holds(condition: dict, arguments: dict) -> bool:
    field = condition.get("field")
    if field not in arguments or arguments[field] is None:
        return False
    actual = arguments[field]
    expected = condition.get("value")
    operator = condition.get("operator")
    try:
        if operator == ">":
            return float(actual) > float(expected)
        if operator == ">=":
            return float(actual) >= float(expected)
        if operator == "<":
            return float(actual) < float(expected)
        if operator == "<=":
            return float(actual) <= float(expected)
        if operator == "==":
            return _equals(actual, expected)
        if operator == "!=":
            return not _equals(actual, expected)
        if operator == "in":
            return _is_in(actual, expected)
    except (TypeError, ValueError):
        return False
    return False


def _equals(actual: Any, expected: Any) -> bool:
    if isinstance(actual, (int, float)) or isinstance(expected, (int, float)):
        try:
            return float(actual) == float(expected)
        except (TypeError, ValueError):
            return False
    return str(actual) == str(expected)


def _is_in(actual: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_equals(actual, item) for item in expected)
    return _equals(actual, expected)
