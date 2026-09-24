"""Write the dashboard sentence for a block or a hold. Does not change the verdict."""

from __future__ import annotations

from ..llm import guided_json

_SCHEMA = {
    "type": "object",
    "properties": {"explanation": {"type": "string"}},
    "required": ["explanation"],
}


async def explain(policy: dict | None, arguments: dict, decision: str) -> str:
    fallback = ""
    if policy:
        fallback = policy.get("original_text") or policy.get("name") or ""
    if not policy:
        return fallback or decision
    try:
        result = await guided_json(
            (
                "You explain a policy decision to a store manager. "
                "Use one or two plain sentences. Say what was requested and why "
                "the policy stopped it or held it. Do not change the decision."
            ),
            (
                f"Decision: {decision}\n"
                f"Policy: {policy.get('name')}\n"
                f"Policy text: {policy.get('original_text')}\n"
                f"Request fields: {arguments}"
            ),
            _SCHEMA,
        )
    except Exception:
        return fallback
    text = result.get("explanation") if isinstance(result, dict) else None
    if isinstance(text, str) and text.strip():
        return text.strip()
    return fallback
