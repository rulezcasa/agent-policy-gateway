# Backend - Agent Policy Gateway

Not built yet. Planned layout (FastAPI-style, subject to change):

```
backend/
	app/
		api/        # HTTP routes: policy upload, policy CRUD, action feed, approvals
		ingestion/  # PDF text extraction + LLM rule extraction -> canonical policy JSON
		engine/     # Policy retrieval + two-stage validation (LLM reasoning + deterministic rule engine)
		gateway/    # MCP interception layer - sits between agents and tool servers
		models/     # DB models / persistence (MongoDB - see ../DATA_MODELS.md)
	tests/
```

Decisions returned by the gateway: `allow` | `block` | `requires_approval`.

See `../DATA_MODELS.md` for collections and canonical formats, and
`../AGENT_USECASE.md` for the demo company, policies, and agents.

## Current implementation

The FastAPI business API follows `../API_CONTRACTS.md`. The deterministic policy
gateway follows `../AGENT_USECASE_NEW.md`. Business endpoints execute operations;
agents should call `/gateway/check` first.

## Run

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.main
```

OpenAPI is available at `http://localhost:8000/docs`.
No direct `uvicorn` command is required; the Python entrypoint starts the ASGI
server internally.

## Test

```bash
cd backend
python -m pytest -q
```

The service uses in-memory demo data for the hackathon scenarios. Restarting the
process resets the data.

## Gateway endpoints

- `POST /gateway/check` - evaluate an agent action.
- `GET /gateway/actions` - list intercepted actions.
- `GET /gateway/decisions` - list decisions.
- `GET /gateway/policies` - list active demo policies.
- `GET /gateway/approvals` - list unresolved approval requests.
- `POST /gateway/approvals/{action_id}` - approve or reject a pending action.

The gateway enforces the nine scenarios in `AGENT_USECASE_NEW.md`. It does not
call the business API yet; it returns the decision and canonical action data for
the MCP interception layer to use.
