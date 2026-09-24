"""JSON files for intercepted actions, held tasks, and the live workflow snapshot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

import fcntl

DB_DIR = Path(__file__).resolve().parents[1] / "db"
POLICIES_PATH = DB_DIR / "policies.json"
ACTIONS_PATH = DB_DIR / "actions.json"
PENDING_PATH = DB_DIR / "pending_tasks.json"
WORKFLOW_PATH = DB_DIR / "workflow_state.json"


def read_policies() -> list[dict]:
    data = _read(POLICIES_PATH, [])
    return data if isinstance(data, list) else []


def read_actions() -> list[dict]:
    data = _read(ACTIONS_PATH, [])
    return data if isinstance(data, list) else []


def read_pending() -> list[dict]:
    data = _read(PENDING_PATH, [])
    return data if isinstance(data, list) else []


def read_workflow_state() -> dict:
    data = _read(WORKFLOW_PATH, {})
    return data if isinstance(data, dict) else {}


def write_workflow_state(state: dict) -> None:
    def replace(current: dict) -> None:
        current.clear()
        current.update(state)

    _locked_update(WORKFLOW_PATH, {}, replace)


def append_action(action: dict) -> dict:
    def add(actions: list) -> None:
        actions.append(action)

    _locked_update(ACTIONS_PATH, [], add)
    return action


def append_pending(task: dict) -> dict:
    def add(tasks: list) -> None:
        tasks.append(task)

    _locked_update(PENDING_PATH, [], add)
    return task


def get_pending(action_id: str) -> dict | None:
    for task in read_pending():
        if task.get("action_id") == action_id:
            return task
    return None


def latest_pending_approval(since: str) -> dict | None:
    matches = [
        task
        for task in read_pending()
        if task.get("status") == "pending_approval" and task.get("created_at", "") >= since
    ]
    return matches[-1] if matches else None


def latest_customer_message(since: str) -> str | None:
    matches = [
        action.get("customer_message")
        for action in read_actions()
        if action.get("timestamp", "") >= since and action.get("customer_message")
    ]
    return matches[-1] if matches else None


def actions_since(since: str) -> list[dict]:
    return [action for action in read_actions() if action.get("timestamp", "") >= since]


def claim_pending(action_id: str) -> dict | None:
    found: dict[str, Any] = {}

    def claim(tasks: list) -> None:
        for task in tasks:
            if task.get("action_id") == action_id and task.get("status") == "pending_approval":
                task["status"] = "executing"
                found["task"] = json.loads(json.dumps(task))
                return

    _locked_update(PENDING_PATH, [], claim)
    return found.get("task")


def release_pending(action_id: str) -> None:
    def release(tasks: list) -> None:
        for task in tasks:
            if task.get("action_id") == action_id and task.get("status") == "executing":
                task["status"] = "pending_approval"
                return

    _locked_update(PENDING_PATH, [], release)


def mark_executed(action_id: str, tool_result: Any, by: str, at: str) -> dict:
    updated: dict[str, Any] = {}

    def finish(tasks: list) -> None:
        for task in tasks:
            if task.get("action_id") == action_id:
                task["status"] = "executed"
                task["tool_result"] = tool_result
                task["resolution"] = {"by": by, "outcome": "approved", "at": at}
                updated["task"] = json.loads(json.dumps(task))
                return

    _locked_update(PENDING_PATH, [], finish)
    if "task" not in updated:
        raise KeyError(f"Unknown action_id: {action_id}")
    return updated["task"]


def mark_rejected(action_id: str, by: str, at: str) -> dict | None:
    """Reject a pending task. Returns the row, or None when the id is unknown.

    A row that is no longer pending is left as it is.
    """
    found: dict[str, Any] = {}

    def reject(tasks: list) -> None:
        for task in tasks:
            if task.get("action_id") != action_id:
                continue
            if task.get("status") == "pending_approval":
                task["status"] = "rejected"
                task["resolution"] = {"by": by, "outcome": "rejected", "at": at}
            found["task"] = json.loads(json.dumps(task))
            return

    _locked_update(PENDING_PATH, [], reject)
    return found.get("task")


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return default
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _locked_update(path: Path, default: Any, mutator: Callable[[Any], None]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            handle.seek(0)
            raw = handle.read().strip()
            data = json.loads(raw) if raw else default
            mutator(data)
            handle.seek(0)
            handle.truncate()
            handle.write(json.dumps(data, indent=2))
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
