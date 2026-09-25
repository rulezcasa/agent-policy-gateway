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
    action_names = [t["name"] for t in tool_manifest] + ["*", "unmatched"]
    category_names = [c["name"] for c in categories]

    rule_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "category": {"type": "string", "enum": category_names},
            "subject_roles": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1,
                "items": {"type": "string", "enum": ["ai_agent"]},
            },
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
        'below when the rule is about one tool. Use "*" when the rule applies to '
        "every tool, including a rule that forbids acting on someone else's order. "
        'Use "unmatched" only when no tool and "*" both fail.\n'
        "- subject_roles: always exactly [\"ai_agent\"]. The gateway checks every "
        "call as ai_agent. Do not emit support_staff, customer, support_agent, "
        "automated_assistant, or automated_assistants.\n"
        "- conditions: tests the engine can compare to real values. Use a tool "
        "parameter name, or one of these fields the gateway adds before comparison: "
        "order_owner_mismatch (boolean), days_since_ordered_on (integer), fulfillment_status "
        "(processing, dispatched, delivered, cancelled), ordered_on, amount, "
        "currency, payment_method, order_customer_id, caller_customer_id. "
        "Values must be numbers, booleans, or those exact status strings. "
        "Never use a set name such as orders_not_owned_by_current_customer or "
        "orders_with_status_processing.\n"
        "- An order that does not belong to the customer on this phone is one "
        "rule: action \"*\", subject_roles [\"ai_agent\"], condition "
        "order_owner_mismatch == true, decision block.\n"
        "- A status gate uses fulfillment_status. Before dispatch is "
        "fulfillment_status == \"processing\". After dispatch is "
        "fulfillment_status in [\"dispatched\", \"delivered\"].\n"
        "- decision: allow, block, or requires_approval.\n"
        "- approval_role: who can approve, only when decision is requires_approval.\n"
        "- A sentence that says there are no exceptions to an amount table is not "
        "its own unconditional block. Encode each tier as an amount condition.\n"
        "- original_text: the literal sentence(s) this rule was extracted from.\n\n"
        f"Available agent tools:\n{tools_summary}"
    )
    user_prompt = f"Policy document:\n{doc_text}"

    result = await guided_json(system_prompt, user_prompt, schema)
    return result["rules"]
