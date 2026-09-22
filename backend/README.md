# Backend — Maplewood Business API

FastAPI service for Maplewood Home & Living. Endpoints follow
[`../API_CONTRACTS.md`](../API_CONTRACTS.md). The API does not enforce policy;
that layer will sit in front of these routes later.

## Layout

```
backend/
  app/
    main.py                 # FastAPI app + /health
    api/
      router.py             # HTTP endpoints
    services/
      service.py            # refunds, discounts, cancels, lookups
    db/
      schema.py             # tables + seed rows
      queries.py            # SQLite reads/writes
    models/
      models.py             # request/response shapes
    tools/                  # MCP tool server
  tests/
    test_business_api.py
    conftest.py             # isolated temp SQLite database per test
```

Request flow:

```
HTTP → api/router.py → services/service.py → db/queries.py → maplewood.db
```

Demo customers, orders, and credit applications are seeded on first run into
`maplewood.db`. Override the path with `MAPLEWOOD_DB_PATH` if needed.

## Run

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.main
```

OpenAPI is at `http://localhost:8000/docs`.

## Test

```bash
cd backend
python -m pytest -q
```
