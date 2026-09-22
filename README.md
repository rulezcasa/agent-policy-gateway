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
- [API_CONTRACTS.md](API_CONTRACTS.md) — the business-system HTTP API contract
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
│   └── app/
│       ├── main.py                # FastAPI app
│       ├── api/                   # HTTP routes
│       ├── services/              # refunds, discounts, cancels, lookups
│       ├── db/                    # SQLite schema, seed data, queries
│       ├── models/                # request/response shapes
│       └── tools/                 # MCP tool server
│
├── test-policies/             # sample unstructured policy PDFs for the demo company
│   └── source/                # plain-text sources (edit + regenerate PDFs from these)
├── AGENT_USECASE.md           # demo company, policies, agents, live demo script
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

The current demo backend is the policy-neutral business API. Customers, orders, and
credit applications live in SQLite (`backend/maplewood.db`). The policy gateway is
not wired yet.

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
python -m app.main
```

This uses the active Python environment and starts the FastAPI server at
`http://127.0.0.1:8000`.

