# Agent Policy Gateway

**A policy firewall for AI agents. Every tool call is checked against your company's own policies, on your own hardware, before it runs.**

Agent → **Policy Gateway** → Tools. Each call is **allowed**, **blocked**, or **held for a human to approve**.**Problem.** Businesses are adopting AI agents to automate day-to-day operations: refunds, orders, customer messaging, CRM but a staff operating it. Company policy still lives in PDFs and internal memos, and the tool path never checks it. An agent can refund past the limit, export a customer list, or cancel an order the courier already has.

**The problem** : Compliance breaks where a written policy meets an action. Operational policies live in PDFs and memoss and people follow them through training and approvals. An AI agent has neither, and the tools it calls only check that a request is valid, not that it's allowed. So a policy-breaking action just goes through, with no error and no alerts. 

Large companies fill that gap with governance and security teams. Most small and medium businesses don't have one, so they connect the agent straight to their CRM and payment APIs.

**The solution** 
Agent Policy Gateway is that missing layer. It sits between the agent and its tools.

```
Agent  →  MCP Policy Gateway  →  MCP Tool Server  →  Business System
                 │
                 └── Admin dashboard (flags, approvals, policy management)
```

## References

- [USECASE.md](AGENT_USECASE.md) — the demo use case, its policies  and its agents.
- [API.md](API.md) — business API contracts
- [DATA_MODELS.md](DATA_MODELS.md) — data storage, collections, and canonical formats

## Directory structure

```
agent-policy-gateway/
├── frontend/                      # Next.js admin dashboard
│   └── src/
│       ├── app/
│       │   ├── dashboard/         # overview (placeholder)
│       │   ├── policies/          # browse structured policies (placeholder)
│       │   │   ├── upload/        # upload unstructured policy PDFs
│       │   │   └── review/        # confirm LLM-extracted rules
│       │   ├── actions/           # live feed of intercepted agent tool calls
│       │   └── approvals/         # holds awaiting a human decision
│       ├── components/            # placeholders (.gitkeep)
│       │   ├── layout/
│       │   ├── policies/
│       │   ├── actions/
│       │   └── ui/                # shadcn/ui installs here
│       └── lib/
│           ├── types.ts           # shared shapes (see DATA_MODELS.md)
│           ├── api.ts             # fetch client for the backend
│           └── mock-data.ts       # fake data for pages not wired yet
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + /health
│   │   ├── settings.py            # LLM model, base URL, MCP server URL
│   │   ├── llm.py                 # guided JSON calls to Ollama
│   │   ├── api/
│   │   │   └── router.py          # business HTTP, ingestion, actions, approvals
│   │   ├── services/
│   │   │   └── service.py         # refunds, discounts, cancels, lookups
│   │   ├── models/
│   │   │   └── models.py          # request/response shapes
│   │   ├── db/
│   │   │   ├── schema.py          # SQLite tables + seed rows
│   │   │   ├── queries.py         # SQLite reads/writes (maplewood.db)
│   │   │   ├── policies.json      # canonical rules (gitignored)
│   │   │   ├── categories.json    # categories from ingestion (gitignored)
│   │   │   ├── documents/         # one JSON file per uploaded policy (gitignored)
│   │   │   ├── actions.json       # every intercepted tool call (gitignored)
│   │   │   ├── pending_tasks.json # blocks and approval holds (gitignored)
│   │   │   └── workflow_state.json # live chat snapshot (gitignored)
│   │   ├── tools/
│   │   │   ├── mcp_server.py      # business MCP tools, no policy (port 8001)
│   │   │   └── __main__.py        # python -m app.tools
│   │   ├── gateway/
│   │   │   ├── mcp_gateway.py     # same tool names, policy in front (port 8002)
│   │   │   ├── intercept.py       # normalize, evaluate, explain, allow/block/hold
│   │   │   ├── forward.py         # forward an allowed call to the tool server
│   │   │   ├── approvals.py       # resume or reject a held call
│   │   │   └── __main__.py        # python -m app.gateway
│   │   ├── policy_engine/
│   │   │   ├── normalize.py       # tool call → fields policies compare
│   │   │   ├── evaluator.py       # deterministic allow / block / requires_approval
│   │   │   ├── explain.py         # dashboard sentence; does not change the verdict
│   │   │   └── store.py           # locked JSON reads/writes
│   │   ├── ingestion/
│   │   │   ├── pipeline.py        # PDF text extraction, write policies under app/db/
│   │   │   └── extraction.py      # LLM split of a document into rules
│   │   ├── agents/
│   │   │   ├── orchestrator.py    # route a chat turn to support or orders
│   │   │   ├── support_agent.py
│   │   │   ├── order_agent.py
│   │   │   ├── state.py           # live chat snapshot
│   │   │   ├── prompts/           # orchestrator, support, and order markdown
│   │   │   └── utils/
│   │   └── utils/
│   │       └── model_json.py      # parse model JSON
│   ├── tests/
│   │   ├── test_evaluator.py      # policy verdicts
│   │   ├── test_approvals.py      # hold, approve, reject
│   │   ├── dummy_chat.py          # scripted agent chat
│   │   └── real_pipeline.py       # ingestion against the sample PDFs
│   ├── maplewood.db               # created on first run (gitignored)
│   └── requirements.txt
│
├── test-policies/                 # sample unstructured policy PDFs
│   ├── generate_pdfs.py           # rebuild PDFs from source/
│   └── source/                    # plain-text sources
├── USECASE.md                     # demo company, policies, agents
├── API.md                         # business-system HTTP API contract
└── DATA_MODELS.md                 # JSON stores and canonical fields
```

## Tech stack

**Frontend**

- Next.js 16 (App Router) + React 19 + TypeScript
- Tailwind CSS 4
- shadcn/ui planned; `src/components/` is still empty placeholders
- `/actions` and `/approvals` poll the API. Dashboard, policies, upload, and review are still placeholders

**Backend**

- Python + FastAPI for the business HTTP API
- SQLite (`backend/maplewood.db`) for customers, orders, and credit applications
- MCP tool server on port 8001 (`python -m app.tools`): same actions as HTTP, no policy checks
- MCP policy gateway on port 8002 (`python -m app.gateway`): same tool names, intercepts every call
- Ollama (`qwen3.6-35b-q8-tools`) for PDF rule extraction, argument normalization and gateway checks.
- LangChain agents (orchestrator, support, order) call the gateway over MCP
- pdfplumber for policy PDF text

Agents reach the business system only through the gateway:

```
Agent → gateway (8002) → policy_engine → allow → tools (8001) → service.py → maplewood.db
                              │
                              └── block / hold → actions.json, pending_tasks.json
```

HTTP calls the service layer directly for business data, and also serves ingestion,
the action feed, and approvals:

```
HTTP → app/api/router.py → app/services/service.py → app/db/queries.py → maplewood.db
```



## User flow

**Phase 1 — one-time setup (company admin)**

1. Admin uploads the company's unstructured policy docs (PDFs).
2. The ingestion engine extracts text, and splits it into individual rules, classifies each into a category automatically based  on your MCP.
3. Admin reviews each extracted rule and aproves, edits or rejects it. Confirmed rules become `active`; only active rules are enforced.

**Phase 2 — runtime enforcement (agents)**

1. Agents connect to the gateway instead of directly to business tools. The gateway
  acts as a proxy and exposes the same MCP tool definitions.
2. Every tool call is intercepted. The gateway adds context from the business system, then an LLM rewrites the call into the fields policies to compare. 
3. The rule engine compares that action to active policies. It checks the caller's role, evaluates each condition, and applies priority. No matching rule means allow. Otherwise it returns `allow` | `block` | `requires_approval`.
4. On a block or a hold, an LLM call writes the explainablility for the UI and the agent. That LLM isn't given full control to change the verdict, the rule-engine enforces determinism.
5. Allowed calls are forwarded to the tool server and the agent loop completes as usual
## Run the frontend

```bash
cd frontend && npm run dev
```

## Run the backend

Install once:

```bash
cd backend
python -m pip install -r requirements.txt
```


**FastAPI** — business HTTP API, ingestion, the action feed, and approvals. `http://localhost:8000/api`. OpenAPI is at `http://localhost:8000/docs`.

```bash
cd backend
python -m app.main
```

**MCP tool server** — the business tools, on port 8001 (`/mcp`). Same tools as the HTTP API. Writes to the same SQLite database. The port is fixed.

```bash
cd backend
python -m app.tools
```

**MCP policy gateway** — same tool names, policy in front. Agents connect here. `http://127.0.0.1:8002/mcp`.

```bash
cd backend
python -m app.gateway
```

| Env | Default | Used by |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | FastAPI |
| `PORT` | `8000` | FastAPI |
| `MAPLEWOOD_DB_PATH` | `backend/maplewood.db` | FastAPI and the tool server |
| `GATEWAY_HOST` | `0.0.0.0` | gateway |
| `GATEWAY_PORT` | `8002` | gateway |
| `MCP_SERVER_URL` | `http://127.0.0.1:8001/mcp` | gateway forward, ingestion |
| `GATEWAY_MCP_URL` | `http://127.0.0.1:8002/mcp` | demo agents, when `USE_GATEWAY` is on |
| `LLM_BASE_URL` | `http://100.102.250.115:11434/v1` | ingestion, rewrite, explanation |
| `LLM_MODEL` | `qwen3.6-35b-q8-tools` | ingestion, rewrite, explanation |

Demo agents read `USE_GATEWAY` in `backend/app/settings.py`. Leave it `True` to go through the gateway. Set it to `False` to call the tool server on port 8001 directly, with no policy checks. The CLI chat prints which path it is using.



