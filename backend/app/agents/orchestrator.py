"""Routing orchestrator: classify the message, update state, dispatch to an agent."""

from __future__ import annotations

import json
from collections import deque

from langchain_ollama import ChatOllama

from .prompts import load_prompt
from .refund_agent import invoke_refund_agent
from .state import get_state, update_state
from .support_agent import invoke_support_agent
from .utils import parse_llm_json


SYSTEM_PROMPT = load_prompt("orchestrator")

llm = ChatOllama(
    model="qwen3.6-35b-q8-tools",
    base_url="http://100.102.250.115:11434",
    reasoning=False,
)

async def dispatcher(agent: str | None) -> str:
    if agent == "refund_agent":
        return await invoke_refund_agent()
    if agent == "support_agent":
        return await invoke_support_agent()


async def orchestrate(phone: str, message: str | None = None) -> str:
    """Classify ``message``, update shared state, and return the specialist reply."""
    if not message:
        return "Hi, how can I help you?"

    saved_state = get_state()
    history = deque(saved_state.get("conversation_history") or [], maxlen=10)

    messages = [
        (
            "system",
            f"{SYSTEM_PROMPT}\n\nCurrent orchestrator state:\n{json.dumps(saved_state, indent=2)}",
        ),
        ("human", message),
    ]

    response = await llm.ainvoke(messages)
    llm_state = parse_llm_json(response.content)

    updated_state = {
        "cust_id": saved_state.get("cust_id"),
        "phone": phone,
        "active_agent": llm_state.get("active_agent"),
        "entities": llm_state.get("entities") or {},
        "user_message": message,
    }
    update_state(updated_state)

    reply = await dispatcher(updated_state["active_agent"])

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    updated_state["conversation_history"] = list(history)
    update_state({"conversation_history": updated_state["conversation_history"]})

    return reply
