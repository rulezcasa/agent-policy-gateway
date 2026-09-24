"""Rewrite a tool call into the field shape policies compare against."""

from __future__ import annotations

from ..llm import guided_json

_ARGUMENT_FIELDS = (
    "amount",
    "discount_percent",
    "payment_method",
    "fulfillment_status",
    "ordered_on",
    "reason",
    "order_id",
    "customer_id",
    "destination",
    "currency",
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string"},
        "arguments": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "discount_percent": {"type": "number"},
                "payment_method": {"type": "string"},
                "fulfillment_status": {"type": "string"},
                "ordered_on": {"type": "string"},
                "reason": {"type": "string"},
                "order_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "destination": {"type": "string"},
                "currency": {"type": "string"},
            },
        },
    },
    "required": ["action", "arguments"],
}


async def normalize(tool: str, arguments: dict, order_context: dict | None = None) -> dict:
    """Return `{action, arguments}` for the rule engine.

    Raw tool arguments win when they were actually sent. Order lookup and the
    model only fill fields the call left out. A failed rewrite still returns
    the raw arguments plus the order lookup.
    """
    base = _merge(arguments, order_context, {})
    try:
        result = await guided_json(
            (
                "You rewrite an agent tool call into fields a policy engine can "
                "compare. Do not decide whether the call is allowed. "
                f"Set action to the tool name {tool!r}. "
                "Copy numbers and ids from the call. Fill payment_method, "
                "fulfillment_status, or ordered_on from the order context when "
                "the call omitted them. Leave a field out when you do not know it."
            ),
            (
                f"Tool: {tool}\n"
                f"Arguments: {arguments}\n"
                f"Order context: {order_context or {}}"
            ),
            _SCHEMA,
        )
    except Exception:
        return {"action": tool, "arguments": base}

    model_args = result.get("arguments") if isinstance(result, dict) else None
    if not isinstance(model_args, dict):
        model_args = {}
    filled = {key: model_args[key] for key in _ARGUMENT_FIELDS if key in model_args}
    return {"action": tool, "arguments": _merge(arguments, order_context, filled)}


def _merge(arguments: dict, order_context: dict | None, model_args: dict) -> dict:
    merged = {key: value for key, value in arguments.items() if value is not None}
    for key, value in (order_context or {}).items():
        if value is not None:
            merged.setdefault(key, value)
    for key, value in model_args.items():
        if value is None or value == "":
            continue
        if key not in arguments or arguments.get(key) in (None, ""):
            merged[key] = value
    return merged
