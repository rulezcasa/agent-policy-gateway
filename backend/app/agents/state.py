"""Shared workflow state for agents.

Initialized on FastAPI startup. Agents read/write via get_state / update_state.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_state: dict[str, Any] | None = None


def _default_state() -> dict[str, Any]:
    return {
        "cust_id": None,
        "phone": None,
        "active_agent": None,
        "entities": {},
        "user_message": None,
        "conversation_history": [],
    }


def init_state() -> dict[str, Any]:
    """Create the global state. Call once on FastAPI startup."""
    global _state
    _state = _default_state()
    return deepcopy(_state)


def get_state() -> dict[str, Any]:
    """Return a copy of the current shared state."""
    if _state is None:
        raise RuntimeError("Agent state is not initialized; call init_state() first")
    return deepcopy(_state)


def update_state(updated_state: dict[str, Any]) -> dict[str, Any]:
    """Shallow-merge ``updated_state`` onto the current shared state."""
    global _state
    if _state is None:
        raise RuntimeError("Agent state is not initialized; call init_state() first")

    _state = {**_state, **updated_state}
    return deepcopy(_state)
