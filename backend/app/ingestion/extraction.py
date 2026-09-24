"""Ingestion extraction: tool list, category prompt, and rule prompt.

The Ollama connection is app.llm.guided_json. This file only builds the
prompts and fetches the MCP tool list those prompts are grounded on.
"""

from __future__ import annotations

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from ..llm import guided_json
from ..settings import MCP_SERVER_URL

CONDITION_OPERATORS = [">", ">=", "<", "<=", "==", "!=", "in"]


async def fetch_tool_manifest(server_url: str = MCP_SERVER_URL) -> list[dict]:
    """Query the live MCP tool server (`tools/list`) on every call.

    Each entry is {"name", "description", "parameters"}, where "parameters"
    is the tool's raw JSON-schema input spec — pipeline.py uses it to ground
    conditions[].field against that tool's real argument names.
    """
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        }
        for tool in result.tools
    ]


async def generate_categories(tool_manifest: list[dict], sample_text: str) -> list[dict]:
    """Propose a small category taxonomy for this tenant from its tools plus
    a sample of its policy text. Each entry is {"name", "description"}.
    Called once per tenant, not once per document. Caching the result under
    app/db/categories.json is pipeline.py's job.
    """
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
    result = await guided_json(system_prompt, user_prompt, schema)
    return result["categories"]


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
            "original_text": {"type": "string"},
        },
        "required": [
            "name",
            "category",
            "subject_roles",
            "action",
            "conditions",
            "decision",
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
        "- original_text: the literal sentence(s) this rule was extracted from.\n\n"
        f"Available agent tools:\n{tools_summary}"
    )
    user_prompt = f"Policy document:\n{doc_text}"

    result = await guided_json(system_prompt, user_prompt, schema)
    return result["rules"]
