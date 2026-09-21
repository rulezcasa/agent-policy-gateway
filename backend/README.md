# Backend — Agent Policy Gateway

Not built yet. Planned layout (FastAPI-style, subject to change):

```
backend/
  app/
    api/        # HTTP routes: policy upload, policy CRUD, action feed, approvals
    ingestion/  # PDF text extraction + LLM rule extraction → canonical policy JSON
    engine/     # Policy retrieval + two-stage validation (LLM reasoning + deterministic rule engine)
    gateway/    # MCP interception layer — sits between agents and tool servers
    models/     # DB models / persistence (MongoDB — see ../DATA_MODELS.md)
  tests/
```

Decisions returned by the gateway: `allow` | `block` | `requires_approval`.

See `../DATA_MODELS.md` for collections and canonical formats, and
`../AGENT_USECASE.md` for the demo company, policies, and agents.
