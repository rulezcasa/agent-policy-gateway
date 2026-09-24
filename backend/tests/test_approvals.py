"""Approval forwarding. The tool server is a fake, so this never opens MCP."""

import asyncio

from app.policy_engine import store
from app.gateway.approvals import resolve_approval


def _use_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "PENDING_PATH", tmp_path / "pending_tasks.json")


def _task(action_id="act_1"):
    return {
        "action_id": action_id,
        "status": "pending_approval",
        "tool": "issue_refund",
        "arguments": {"order_id": "ORD-1", "amount": 150},
        "decision": "requires_approval",
    }


def test_approve_forwards_once(monkeypatch, tmp_path):
    _use_tmp(monkeypatch, tmp_path)
    store.append_pending(_task())
    calls = []

    async def forward(tool, arguments):
        calls.append((tool, arguments))
        return "refunded"

    first = asyncio.run(resolve_approval("act_1", "approved", "manager_priya", forward))
    second = asyncio.run(resolve_approval("act_1", "approved", "manager_priya", forward))

    assert calls == [("issue_refund", {"order_id": "ORD-1", "amount": 150})]
    assert first["status"] == "executed"
    assert first["tool_result"] == "refunded"
    assert first["resolution"]["outcome"] == "approved"
    assert second["status"] == "executed"
    assert second["tool_result"] == "refunded"


def test_reject_does_not_forward(monkeypatch, tmp_path):
    _use_tmp(monkeypatch, tmp_path)
    store.append_pending(_task("act_2"))
    calls = []

    async def forward(tool, arguments):
        calls.append(tool)
        return "should-not-run"

    task = asyncio.run(resolve_approval("act_2", "rejected", "manager_priya", forward))
    assert calls == []
    assert task["status"] == "rejected"
    assert task["resolution"]["outcome"] == "rejected"
