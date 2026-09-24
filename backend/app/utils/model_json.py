"""Parse model text and build the Ollama chat URL."""

from __future__ import annotations

import json
import re

from ..settings import LLM_BASE_URL

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def ollama_chat_url() -> str:
    """Native /api/chat URL. The /v1 shim ignores think:false."""
    base = LLM_BASE_URL.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/api/chat"


def extract_json(content: str) -> dict:
    """Parse a JSON object after stripping a <think> block."""
    cleaned = _THINK_BLOCK_RE.sub("", content).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Model response wasn't valid JSON after stripping <think> blocks. "
            f"Raw content (first 1000 chars): {content[:1000]!r}"
        ) from exc


def parse_llm_json(content: object) -> dict:
    """Parse a JSON object from agent content, including markdown fences."""
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    text = str(content).replace("```json", "").replace("```", "").strip()
    return json.loads(text)
