"""Send an allowed or approved tool call to the Maplewood MCP tool server."""

from __future__ import annotations

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from ..settings import MCP_SERVER_URL


async def forward_tool(tool: str, arguments: dict, server_url: str = MCP_SERVER_URL) -> str:
    payload = {key: value for key, value in arguments.items() if value is not None}
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, payload)
    text = _result_text(result)
    if getattr(result, "isError", False):
        raise RuntimeError(text or f"{tool} failed")
    return text


def _result_text(result) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)
