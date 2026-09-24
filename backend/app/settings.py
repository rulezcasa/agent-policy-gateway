"""Environment shared by ingestion and the gateway."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Same server and model as ChatOllama in the agents (reasoning=False).
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://100.102.250.115:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.6-35b-q8-tools")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")
GATEWAY_MCP_URL = os.environ.get("GATEWAY_MCP_URL", "http://127.0.0.1:8002/mcp")

# Demo switch. Flip this to show the same chat with and without policy checks.
# True  → agents call the gateway (8002): allow / block / hold.
# False → agents call the tool server (8001) directly: every call runs.
USE_GATEWAY = True


def agent_mcp_url() -> str:
    """MCP endpoint the demo agents connect to."""
    return GATEWAY_MCP_URL if USE_GATEWAY else MCP_SERVER_URL
