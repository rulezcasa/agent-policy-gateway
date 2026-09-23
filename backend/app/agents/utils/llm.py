"""LLM response helpers."""

from __future__ import annotations

import json


def parse_llm_json(content: object) -> dict:
    """Normalize model content and parse a JSON object (strips markdown fences)."""
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    text = str(content).replace("```json", "").replace("```", "").strip()
    return json.loads(text)
