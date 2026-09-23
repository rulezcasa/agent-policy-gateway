# Ingestion

Turns uploaded policy PDFs into structured, enforceable policy rules — the
Phase 1 pipeline described in the root [README.md](../../../README.md) and
[DATA_MODELS.md](../../../DATA_MODELS.md). Everything here runs against a
model served locally (ZGX Nano via ZRT/vLLM) — no cloud LLM calls.

```
PDF(s) → text + tables extraction → tool manifest + category taxonomy
       → guided-JSON extraction (one call per doc, all concurrent)
       → grounding validation → documents.json / policies.json
```

## Files

**`llm_client.py`** — everything that talks to something outside this
process: the model on the Nano, and the MCP tool server exposing the
business tools. Has no idea PDFs exist.

- `fetch_tool_manifest()` — connects as an MCP client, calls `tools/list`,
  caches the result. This is how `action` grounding stays plug-and-play
  instead of hardcoded to one company's tools.
- `get_or_generate_categories(tool_manifest, sample_text)` — one LLM call
  that proposes a small category taxonomy from the tool manifest + a sample
  of policy text, cached. Called once per tenant, not once per document.
- `extract_rules_from_text(doc_text, tool_manifest, categories)` — the main
  extraction call. Builds a JSON schema constraining `action`/`category` to
  the two lists above, sends a structured-output request (`response_format:
  json_schema`, thinking disabled), returns raw rule dicts.

**`pipeline.py`** — orchestration: PDFs in, validated entries in
`documents.json`/`policies.json` out. `process_documents(file_paths)` is the
entrypoint an upload endpoint would call once one exists.

- `extract_text(pdf_path)` — pdfplumber: plain text + tables (tables
  rendered as Markdown so the LLM parses them reliably). Text-only for now,
  no vision/OCR fallback — fine for the documents this ingests today.
- `_validate_rule(rule, tool_manifest)` — the safety net. Checks a rule's
  `action` is a real tool name and every `conditions[].field` matches that
  tool's real arguments (or a known gateway-enriched field, e.g.
  `fulfillment_status`). A rule that fails this is still saved, just flagged
  `needs_review: true` — it never silently disappears or silently gets
  wired to a condition that can never fire.
- `_build_policy(rule, doc_id, needs_review)` — assigns `policy_id`,
  `version: 1`, and **`status: "pending_review"` always** — extraction never
  marks a rule `active`. That transition happens later, when a human
  confirms it on `/policies/review`.

## How multiple documents are actually processed

Given N PDFs, only two stages scale with N — everything else happens once
for the whole batch, not once per document:

| Stage | Behavior |
|---|---|
| Text extraction | All N concurrently (thread pool, `max_workers=len(file_paths)`) |
| Document records write | One batched write |
| Tool manifest fetch | Once for the whole batch |
| Category taxonomy | Once for the whole batch, from **one** sample document's text |
| LLM rule extraction | All N concurrently (`asyncio.gather`) |
| Validation + ID assignment | Sequential loop, but no network call — negligible cost |
| Policies write | One batched write |

"Concurrent" extraction means N requests in flight at once against a
*single* model instance — vLLM's continuous batching handles the actual
parallelism server-side. This never spins up multiple model copies, and
there's no hardcoded document count anywhere; `process_documents` sizes
itself off `len(file_paths)`.

Not yet handled: a genuinely huge document (chunking was scoped out —
single-shot per document, since 262K context makes it a non-issue for
realistic policy docs) and unbounded batch sizes (no concurrency cap yet;
fine at small-to-moderate batch sizes, worth revisiting if this ever needs
to process very large batches at once).

## Config

Read from `backend/.env` (gitignored — see `backend/.env.example` for the
template):

```
LLM_BASE_URL   # OpenAI-compatible endpoint for the model served on the Nano
LLM_MODEL      # exact model name as `zrt status` reports it (SERVED AS column)
MCP_SERVER_URL # the MCP tool server exposing the business tools
```

## Data produced

All under `backend/data/` (gitignored, generated at runtime):

- `documents.json` — one record per uploaded PDF (raw text, status)
- `policies.json` — one record per extracted rule (`status: "pending_review"`
  until a human confirms it elsewhere)
- `tool_manifest.json` — cached MCP tool list
- `categories.json` — cached category taxonomy

## Running it

```bash
cd backend
pip install -r requirements.txt
python -m app.ingestion.pipeline                 # test-policies/*.pdf by default
python -m app.ingestion.pipeline path/to/a.pdf …  # or specific files
```

`scripts/test_real_pipeline.py` is a manual smoke-test script that runs the
real pipeline against the real model with only the MCP fetch faked out (no
MCP server running locally yet), and times concurrent vs. serial extraction
to confirm the parallelism is actually doing something.

```bash
python -m scripts.test_real_pipeline
```
