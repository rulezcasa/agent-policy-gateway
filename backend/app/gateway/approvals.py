"""Approve or reject a held tool call. Approval forwards it once."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Awaitable, Callable

from ..policy_engine.store import claim_pending, get_pending, mark_executed, mark_rejected, release_pending

Forward = Callable[[str, dict], Awaitable[str]]


async def resolve_approval(
    action_id: str,
    outcome: str,
    by: str,
    forward: Forward | None = None,
) -> dict:
    at = datetime.now(timezone.utc).isoformat()
    if outcome == "rejected":
        task = mark_rejected(action_id, by, at)
        if task is None:
            raise KeyError(f"Unknown action_id: {action_id}")
        return task

    claimed = claim_pending(action_id)
    if claimed is None:
        existing = get_pending(action_id)
        if existing is None:
            raise KeyError(f"Unknown action_id: {action_id}")
        return existing

    if forward is None:
        from .forward import forward_tool

        forward = forward_tool
    try:
        result = await forward(claimed["tool"], claimed.get("arguments") or {})
    except Exception:
        release_pending(action_id)
        raise
    return mark_executed(action_id, result, by, at)
