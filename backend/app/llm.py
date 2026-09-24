"""One guided-JSON call to the shared Ollama model.

Ingestion and the policy engine both use this. Prompts stay in the caller.
"""

from __future__ import annotations

import httpx

from .settings import LLM_MODEL
from .utils.model_json import extract_json, ollama_chat_url


async def guided_json(system_prompt: str, user_prompt: str, schema: dict) -> dict:
    """Return the model's JSON object for one system/user prompt pair."""
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "think": False,
        "format": schema,
        "options": {"temperature": 0.2, "num_predict": 4096},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
        response = await client.post(ollama_chat_url(), json=payload)
        response.raise_for_status()
        data = response.json()

    message = data.get("message") or {}
    content = message.get("content") or ""
    if not content:
        raise RuntimeError(
            f"Model returned no content (done_reason={data.get('done_reason')!r}). "
            f"thinking={message.get('thinking')!r}"
        )
    return extract_json(content)
