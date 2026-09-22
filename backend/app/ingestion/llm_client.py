"""Talks to the two external systems ingestion depends on: the model served
on the ZGX Nano, and the MCP tool server exposing the business tools.

Nothing here reads a PDF or writes to policies.json — that orchestration
lives in pipeline.py. This module only knows how to fetch the tool manifest,
generate/cache a category taxonomy, and run one guided-JSON extraction call.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AsyncOpenAI

load_dotenv()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TOOL_MANIFEST_PATH = DATA_DIR / "tool_manifest.json"
CATEGORIES_PATH = DATA_DIR / "categories.json"

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:8080/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "nvidia/Qwen3.6-35B-A3B-NVFP4")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")

CONDITION_OPERATORS = [">", ">=", "<", "<=", "==", "!=", "in"]

_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key="EMPTY")


def _read_cache(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _write_cache(path: Path, data: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


async def fetch_tool_manifest(
    server_url: str = MCP_SERVER_URL, *, force_refresh: bool = False
) -> list[dict]:
    """Query the MCP tool server for its tool list and cache the result.

    Each entry is {"name", "description", "parameters"}, where "parameters"
    is the tool's raw JSON-schema input spec — pipeline.py uses it to ground
    conditions[].field against that tool's real argument names.
    """
    if not force_refresh:
        cached = _read_cache(TOOL_MANIFEST_PATH)
        if cached is not None:
            return cached

    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()

    manifest = [
        {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        }
        for tool in result.tools
    ]
    _write_cache(TOOL_MANIFEST_PATH, manifest)
    return manifest


async def get_or_generate_categories(
    tool_manifest: list[dict], sample_text: str, *, force_refresh: bool = False
) -> list[dict]:
    """Propose a small category taxonomy for this tenant from its tools plus
    a sample of its policy text, and cache it. Each entry is
    {"name", "description"}. Called once per tenant, not once per document.
    """
    if not force_refresh:
        cached = _read_cache(CATEGORIES_PATH)
        if cached is not None:
            return cached

    tools_summary = "\n".join(f"- {t['name']}: {t['description']}" for t in tool_manifest)
    schema = {
        "type": "object",
        "properties": {
            "categories": {
                "type": "array",
                "minItems": 3,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["name", "description"],
                },
            }
        },
        "required": ["categories"],
    }
    system_prompt = (
        "You design policy-category taxonomies for an AI-agent governance system. "
        "Given the tools a company's agents can call and a sample of their policy "
        "documents, propose 3-10 short category labels (snake_case) that usefully "
        "group that company's policy rules for filtering in a dashboard. Base the "
        "categories on this company's actual domain, not a generic list."
    )
    user_prompt = (
        f"Available agent tools:\n{tools_summary}\n\n"
        f"Sample policy text:\n{sample_text[:4000]}"
    )
    result = await _guided_json(system_prompt, user_prompt, schema)
    categories = result["categories"]
    _write_cache(CATEGORIES_PATH, categories)
    return categories


async def extract_rules_from_text(
    doc_text: str, tool_manifest: list[dict], categories: list[dict]
) -> list[dict]:
    """Extract structured policy rules from one document's text in a single
    call. Returns raw rule dicts — grounding/validation against the tool
    manifest and writing to policies.json both happen in pipeline.py.
    """
    action_names = [t["name"] for t in tool_manifest] + ["unmatched"]
    category_names = [c["name"] for c in categories]

    rule_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "category": {"type": "string", "enum": category_names},
            "subject_roles": {"type": "array", "items": {"type": "string"}},
            "action": {"type": "string", "enum": action_names},
            "conditions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "operator": {"type": "string", "enum": CONDITION_OPERATORS},
                        "value": {},
                        "unit": {"type": ["string", "null"]},
                    },
                    "required": ["field", "operator", "value"],
                },
            },
            "decision": {"type": "string", "enum": ["allow", "block", "requires_approval"]},
            "approval_role": {"type": ["string", "null"]},
            "priority": {"type": "integer"},
            "original_text": {"type": "string"},
        },
        "required": [
            "name",
            "category",
            "subject_roles",
            "action",
            "conditions",
            "decision",
            "priority",
            "original_text",
        ],
    }
    schema = {
        "type": "object",
        "properties": {"rules": {"type": "array", "items": rule_schema}},
        "required": ["rules"],
    }

    tools_summary = "\n".join(
        f"- {t['name']}({', '.join(t['parameters'].get('properties', {}).keys())}): "
        f"{t['description']}"
        for t in tool_manifest
    )
    system_prompt = (
        "You extract enforceable policy rules from a company's internal policy "
        "document, for an AI-agent governance gateway. Find every distinct rule "
        "that constrains what an AI agent may do, and turn each into one "
        "structured object.\n\n"
        "For each rule:\n"
        '- action: the tool it governs. Use the exact tool name from the list '
        'below if one clearly matches; otherwise use "unmatched".\n'
        "- conditions: machine-checkable tests against that tool's arguments "
        "(prefer field names that match the tool's real parameter names). Leave "
        "empty if the rule always applies once action matches.\n"
        "- decision: allow, block, or requires_approval.\n"
        "- approval_role: who can approve, only when decision is requires_approval.\n"
        "- priority: higher wins when multiple rules could match the same call "
        "(e.g. a stricter dollar threshold should outrank a looser one).\n"
        "- original_text: the literal sentence(s) this rule was extracted from.\n\n"
        f"Available agent tools:\n{tools_summary}"
    )
    user_prompt = f"Policy document:\n{doc_text}"

    result = await _guided_json(system_prompt, user_prompt, schema)
    return result["rules"]


async def _guided_json(system_prompt: str, user_prompt: str, schema: dict) -> dict:
    # response_format/json_schema is the OpenAI-standard structured-output
    # request, which this vLLM version honors — the older guided_json
    # extra_body extension was silently ignored (no error, just plain text).
    response = await _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "extraction_result", "schema": schema, "strict": True},
        },
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )
    choice = response.choices[0]
    content = choice.message.content
    if not content:
        reasoning = getattr(choice.message, "reasoning_content", None)
        raise RuntimeError(
            f"Model returned no content (finish_reason={choice.finish_reason!r}). "
            f"reasoning_content={reasoning!r}"
        )
    return _extract_json(content)


_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _extract_json(content: str) -> dict:
    # Some serving configs don't fully honor enable_thinking=False and still
    # emit a <think>...</think> block ahead of the actual JSON — strip it
    # before parsing rather than assuming content is pure JSON.
    cleaned = _THINK_BLOCK_RE.sub("", content).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Model response wasn't valid JSON after stripping <think> blocks. "
            f"Raw content (first 1000 chars): {content[:1000]!r}"
        ) from exc
