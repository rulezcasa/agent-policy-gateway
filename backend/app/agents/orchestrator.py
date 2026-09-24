"""Routing orchestrator: classify the message, update state, dispatch to an agent."""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone

from langchain_ollama import ChatOllama

from ..policy_engine.store import (
    actions_since,
    get_pending,
    latest_customer_message,
    latest_pending_approval,
    write_workflow_state,
)
from .prompts import load_prompt
from .order_agent import invoke_order_agent
from .state import get_state, update_state
from .support_agent import invoke_support_agent
from .utils import parse_llm_json


SYSTEM_PROMPT = load_prompt("orchestrator")
HOLD_CUSTOMER_MESSAGE = (
    "Your request has been submitted and needs approval. You'll hear back shortly."
)

llm = ChatOllama(
    model="qwen3.6-35b-q8-tools",
    base_url="http://100.102.250.115:11434",
    reasoning=False,
)

async def dispatcher(agent: str | None) -> str:
    if agent == "order_agent":
        return await invoke_order_agent()
    if agent == "support_agent":
        return await invoke_support_agent()
    return "I'm not sure which desk should take that. Could you say a bit more?"


async def orchestrate(phone: str, message: str | None = None) -> dict:
    """Classify ``message``, dispatch, and report a held action id when one was saved."""
    if not message:
        return {"reply": "Hi, how can I help you?", "pending_action_id": None, "customer_message": None}

    started = datetime.now(timezone.utc).isoformat()
    saved_state = get_state()
    history = deque(saved_state.get("conversation_history") or [], maxlen=20)

    messages = [
        (
            "system",
            f"{SYSTEM_PROMPT}\n\nCurrent orchestrator state:\n{json.dumps(saved_state, indent=2)}",
        ),
        ("human", message),
    ]

    response = await llm.ainvoke(messages)
    llm_state = parse_llm_json(response.content)

    history.append({"role": "user", "content": message})
    updated_state = {
        "cust_id": saved_state.get("cust_id"),
        "phone": phone,
        "active_agent": llm_state.get("active_agent"),
        "entities": llm_state.get("entities") or {},
        "user_message": message,
        "conversation_history": list(history),
    }
    update_state(updated_state)
    write_workflow_state(get_state())

    reply = await dispatcher(updated_state["active_agent"])

    turn_actions = actions_since(started)
    customer_message = latest_customer_message(started)
    pending = latest_pending_approval(started)
    shown = _shown_reply(reply, customer_message, pending)
    history.append({"role": "assistant", "content": shown})
    for action in turn_actions:
        if action.get("decision") in {"block", "requires_approval"}:
            history.append({"role": "policy", "content": _policy_note(action)})
    update_state({"conversation_history": list(history)})
    write_workflow_state(get_state())

    return {
        "reply": reply,
        "pending_action_id": pending["action_id"] if pending else None,
        "customer_message": customer_message,
    }


def _shown_reply(reply: str, customer_message: str | None, pending: dict | None) -> str:
    """Text the customer actually saw. History keeps this, not a discarded agent reply."""
    if customer_message:
        return customer_message
    if pending:
        return HOLD_CUSTOMER_MESSAGE
    return reply


def _policy_note(action: dict) -> str:
    """Why a tool call was blocked or held, for the next agent turn."""
    tool = action.get("tool") or "the tool"
    arguments = action.get("arguments") or {}
    order_id = arguments.get("order_id")
    target = f"{tool} ({order_id})" if order_id else tool
    reason = action.get("llm_reasoning") or action.get("customer_message") or "A company policy applies."
    if action.get("decision") == "requires_approval":
        role = action.get("required_approval") or "a manager"
        return (
            f"{target} is held for approval by {role}. {reason} "
            "Do not call this tool again until it is approved."
        )
    return (
        f"{target} was blocked. {reason} "
        "Do not retry this tool for the same request. "
        "If the customer pushes back, explain this reason. "
        "Do not look up a different customer or ask them to confirm the phone number to get around the block."
    )


async def continue_after_approval(action_id: str) -> str:
    """Phrase the approved tool result for the customer. Does not call tools again."""
    task = get_pending(action_id)
    if not task:
        return "I couldn't find that request."
    result_text = task.get("tool_result") or ""
    agent_id = task.get("agent_id") or "order_agent"
    try:
        prompt = load_prompt(agent_id)
    except FileNotFoundError:
        prompt = "You are a Maplewood support assistant.\n"
    messages = [
        (
            "system",
            f"{prompt}\nThe approved tool already ran. "
            "Tell the customer what happened in one or two sentences. Do not call any tools.",
        ),
        ("human", f"Tool {task.get('tool')} result:\n{result_text}"),
    ]
    try:
        response = await llm.ainvoke(messages)
    except Exception:
        return f"Your request was approved. {result_text}"
    content = response.content
    return content if isinstance(content, str) else str(content)
