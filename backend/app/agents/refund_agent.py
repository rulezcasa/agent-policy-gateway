"""Refunds and billing specialist."""

from __future__ import annotations

import json

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from .prompts import load_prompt
from .state import get_state


SYSTEM_PROMPT = load_prompt("refund_agent")


async def invoke_refund_agent() -> str:
    """Handle the current turn for the refund agent."""
    client = MultiServerMCPClient(
        {
            "my_server": {
                "transport": "streamable_http",
                "url": "http://127.0.0.1:8001/mcp",
            },
        }
    )

    tools = await client.get_tools()

    llm = ChatOllama(
        model="qwen3.6-35b-q8-tools",
        base_url="http://100.102.250.115:11434",
        reasoning=False,
    )

    agent = create_agent(llm, tools)

    saved_state = get_state()
    messages = [
        (
            "system",
            f"{SYSTEM_PROMPT}\n\nCurrent refund agent state:\n{json.dumps(saved_state, indent=2)}",
        ),
        ("human", saved_state.get("user_message")),
    ]

    result = await agent.ainvoke({"messages": messages})
    content = result["messages"][-1].content
    return content if isinstance(content, str) else str(content)
