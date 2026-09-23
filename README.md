# Agent Policy Gateway

Private agent governance gateway for SMEs. AI agents are given tool access (refunds,
orders, messaging, CRM), but nothing stops them from doing things the company's
policies forbid. This gateway sits between agents and their tools, intercepts every
tool call, validates it against the company's own policies, and either allows it,
blocks it, or holds it for human approval.

```
Agent  →  MCP Policy Gateway  →  MCP Tool Server  →  Business System
                 │
                 └── Admin dashboard (flags, approvals, policy management)
```

## Documentation

- [AGENT_USECASE.md](AGENT_USECASE.md) — the demo company (Maplewood Home & Living),
  its policies, and the demo agents we'll build for the live demo
- [API.md](API.md) — the business-system HTTP API contract
- [DATA_MODELS.md](DATA_MODELS.md) — data storage, collections, and every
  field of the canonical formats explained

## Directory structure

```
agent-policy-gateway/
├── frontend/                  # Next.js admin dashboard
│   └── src/
│       ├── app/
│       │   ├── dashboard/         # overview stats, recent flags
│       │   ├── policies/          # browse structured policies
│       │   │   ├── upload/        # upload unstructured policy PDFs
│       │   │   └── review/        # confirm LLM-extracted rules (one-time setup)
│       │   ├── actions/           # live feed of intercepted agent tool calls
│       │   └── approvals/         # flagged actions awaiting human decision
│       ├── components/
│       │   ├── layout/            # app shell: sidebar, top bar
│       │   ├── policies/          # upload dropzone, rule review cards, policy table
│       │   ├── actions/           # action feed items, flag/approval cards, decision badges
│       │   └── ui/                # generic primitives (shadcn/ui installs here)
│       └── lib/
│           ├── types.ts           # canonical shapes shared with backend (see DATA_MODELS.md)
│           ├── api.ts             # thin fetch client for the backend
│           └── mock-data.ts       # fake data for building UI before backend exists
│
├── backend/                   # Maplewood business API (gateway comes later)
│   ├── app/
│   │   ├── main.py                # FastAPI app + /health
│   │   ├── api/
│   │   │   └── router.py          # HTTP endpoints under /api
│   │   ├── services/
│   │   │   └── service.py         # refunds, discounts, cancels, lookups
│   │   ├── db/
│   │   │   ├── schema.py          # tables + seed rows
│   │   │   └── queries.py         # SQLite reads/writes
│   │   ├── models/
│   │   │   └── models.py          # request/response shapes
│   │   └── tools/
│   │       ├── mcp_server.py      # MCP tools (1:1 with HTTP actions)
│   │       └── __main__.py        # python -m app.tools
│   ├── tests/                     # isolated temp SQLite database per test
│   ├── maplewood.db               # created on first run (gitignored)
│   └── requirements.txt
│
├── test-policies/             # sample unstructured policy PDFs for the demo company
│   └── source/                # plain-text sources (edit + regenerate PDFs from these)
├── AGENT_USECASE.md           # demo company, policies, agents, live demo script
├── API.md                     # business-system HTTP API contract
└── DATA_MODELS.md             # storage, collections, canonical formats field-by-field
```

## Tech stack

**Frontend**
- Next.js (App Router) + TypeScript
- Tailwind CSS, shadcn/ui planned for components
  pages read from `lib/mock-data.ts` until the backend is wired up

**Backend**
- Python + FastAPI
- LLM for policy extraction (ingestion) and action reasoning (explainability) —
  runs locally/privately, which is part of the pitch
- Deterministic rule engine (plain Python, no LLM) for final enforcement decisions
- MCP-compatible gateway surface so any agent framework can plug in
- MongoDB (or Postgres JSONB) for storing canonical policy documents —
  see [DATA_MODELS.md](DATA_MODELS.md) for the reasoning

The current demo backend is the policy-neutral business API. HTTP shapes are in
[API.md](API.md). Customers, orders, and credit applications are seeded on first
run into SQLite (`backend/maplewood.db`). Override the path with `MAPLEWOOD_DB_PATH`
if needed. The policy gateway is not wired yet.

HTTP and MCP both call the same service layer and write to the same database:

```
HTTP → app/api/router.py       ─┐
MCP  → app/tools/mcp_server.py ─┴→ app/services/service.py → app/db/queries.py → maplewood.db
```

| HTTP | MCP tool |
|---|---|
| `GET /api/customers?phone=` | `get_customer_record` |
| `GET /api/customers/{id}/orders` | `get_orders` |
| `GET /api/orders/{order_id}` | `get_order_status` |
| `POST /api/orders/{order_id}/refunds` | `issue_refund` |
| `POST /api/orders/{order_id}/discounts` | `apply_discount` |
| `GET /api/customers/{id}/credit-application` | `get_credit_application` |
| `POST /api/customers/export` | `export_customer_list` |
| `PUT /api/orders/{order_id}/shipping-address` | `update_shipping_address` |
| `POST /api/orders/{order_id}/cancel` | `cancel_order` |
| `POST /api/orders/{order_id}/return` | `return_order` |

## User flow

**Phase 1 — one-time setup (company admin)**
1. Admin uploads the company's unstructured policy docs (PDFs) at `/policies/upload`.
2. Backend extracts text, and an LLM splits it into individual rules, classifies each
   into a category (payments, customer_data, orders, pricing, communication,
   access_permissions), and converts it into the canonical structured format.
3. Admin reviews each extracted rule at `/policies/review` — original policy text
   side-by-side with the structured version — and confirms, edits, or rejects it.
   Confirmed rules become `active`; only active rules are enforced.

**Phase 2 — runtime enforcement (agents)**
1. Agents connect to the gateway instead of directly to business tools. The gateway
   exposes the same MCP tool definitions.
2. Every proposed tool call is intercepted and converted into a canonical action.
3. Two-stage validation:
   - **Stage A (LLM, explainability only):** interprets what the agent is trying to
     do, which policies apply, and whether anything is ambiguous. Output feeds the
     dashboard narrative — it never gates the action (prompt-injection resistant).
   - **Stage B (deterministic rule engine, final decision):** checks roles, evaluates
     numeric/field conditions, applies priority, and returns
     `allow` | `block` | `requires_approval`.
4. Allowed calls are forwarded to the real tool. Everything else shows up in the UI:
   blocked actions appear as flags, `requires_approval` actions land on `/approvals`
   where a manager approves (gateway then executes) or rejects.

## Run the frontend

```bash
cd frontend && npm run dev
```

## Run the backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.main
```

HTTP API is at `http://localhost:8000/api`. OpenAPI is at `http://localhost:8000/docs`.

| Env | Default | Used by |
|---|---|---|
| `HOST` | `0.0.0.0` | HTTP API |
| `PORT` | `8000` | HTTP API |
| `MAPLEWOOD_DB_PATH` | `backend/maplewood.db` | HTTP API and MCP |

The MCP tool server is a separate process on port 8001 (`/mcp`). It exposes the
same eight actions and writes to the same SQLite database:

```bash
cd backend
python -m app.tools
```

## Test the backend

```bash
cd backend
python -m pytest -q
```

