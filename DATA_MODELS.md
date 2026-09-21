# Data Models

What we store, where, and what every field means. The canonical shapes live in
`frontend/src/lib/types.ts` and the backend must emit exactly these — they are the
contract between the two halves of the system.

## Storage choice: document store (NoSQL) — yes

The canonical policy format is nested JSON with variable shape: `conditions` is an
array of heterogeneous tests, `subject` is a nested object, and different policies
carry different optional fields (`approval_role`, `unit`, ...). Same for actions —
`arguments` is a free-form payload that differs per tool. Flattening this into
relational tables buys nothing for a demo and costs schema-migration time every
time the format evolves mid-hackathon.

**Recommendation: MongoDB** (one `docker run`, zero schema setup). Every canonical
object is stored as-is, queried by the few fields the engine filters on.

> Alternative: Postgres with JSONB columns gives the same document flexibility and
> matches the original design doc — fine choice too. For hackathon speed, Mongo (or
> even TinyDB/SQLite-JSON for a single-process demo) is the path of least friction.
> Nothing in the flow needs joins or transactions.

## Collections

Four collections. Indexes only on the fields the engine actually filters by.

| Collection | Holds | Queried by |
|---|---|---|
| `documents` | Uploaded policy files + extracted raw text | `doc_id` |
| `policies` | Canonical structured rules (one per extracted rule) | `action`, `category`, `status`, `subject.roles` |
| `actions` | Every intercepted agent tool call | `action_id`, `timestamp` (feed ordering) |
| `decisions` | Gateway verdict per action; pending ones are the approval queue | `action_id`, `decision`, `expires_at` |

### `documents`

Stores the original upload (the design doc requires keeping both original + normalized).

```json
{
  "doc_id": "doc_001",
  "filename": "01_refunds_and_payments_policy.pdf",
  "uploaded_at": "2026-09-21T10:00:00Z",
  "raw_text": "LUMINA WELLNESS SPA & CLINIC\nInternal Memo — ...",
  "status": "extracted"   // uploaded | extracting | extracted | failed
}
```

The file itself can sit on disk (`uploads/`) with the path stored here — no need for
GridFS/blob storage in a demo.

### `policies` — one document per rule (canonical policy format)

```json
{
  "policy_id": "refund_limit_001",
  "name": "Refund authorization limit",
  "category": "payments",
  "subject": { "roles": ["support_agent", "ai_agent"] },
  "action": "issue_refund",
  "conditions": [
    { "field": "amount", "operator": ">", "value": 100, "unit": "USD" }
  ],
  "decision": "requires_approval",
  "approval_role": "manager",
  "priority": 90,
  "version": 1,
  "status": "active",
  "source_doc": "doc_001",
  "original_text": "Anything above $100 needs sign-off from a shift manager..."
}
```

Field by field:

| Field | Meaning |
|---|---|
| `policy_id` | Unique ID. Decisions reference it, flag cards link to it. |
| `name` | Human-readable title shown in the UI. |
| `category` | One of six: `payments`, `customer_data`, `scheduling`, `pricing`, `communication`, `access_permissions`. Assigned by the LLM at ingestion; used for UI filtering and as a retrieval fallback key. |
| `subject.roles` | Who the rule binds (`ai_agent`, `support_agent`, ...). A rule limiting the assistant needn't bind a human manager. Matched against `AgentAction.actor_role`. |
| `action` | The tool/action this rule governs (`issue_refund`). Primary retrieval key: an incoming `issue_refund` call fetches all active policies with this action. |
| `conditions` | Array of machine-checkable tests (see below). **All** must hold for the rule to trigger. Empty array = rule always applies to this action (e.g. "no price matching, ever"). |
| `decision` | What happens when the rule triggers: `allow`, `block`, or `requires_approval`. |
| `approval_role` | Who can unblock — only meaningful for `requires_approval` (`manager`, `finance_director`). |
| `priority` | Tiebreaker when several rules match; higher wins. A $600 refund matches both the >$100 and >$500 rules — priority makes the finance-director rule win. |
| `version` | Incremented when an admin edits the rule. Lets a flag say "violated v2". |
| `status` | Lifecycle: `pending_review` (extracted, awaiting human confirmation) → `active` (confirmed, enforced) or `draft` (parked). **Only `active` rules are enforced.** |
| `source_doc` | Which uploaded document this rule came from — traceability in the UI. |
| `original_text` | The raw sentence the rule was extracted from. Shown side-by-side with the JSON on `/policies/review`; this is what makes human confirmation possible. |

#### `conditions[]` (PolicyCondition)

| Field | Meaning |
|---|---|
| `field` | Which key of the action's `arguments` to inspect (`amount`, `discount_percent`, `hours_until_appointment`). |
| `operator` | Comparison: `>`, `>=`, `<`, `<=`, `==`, `!=`, `in`. Plain string, engine implements the small set we need. |
| `value` | Threshold or expected value (`100`, `20`, `"gift_card"`). |
| `unit` | Optional, for display: `USD`, `percent`, `hours`. Lets the UI say "$100" instead of "100". |

### `actions` — one document per intercepted tool call (canonical action format)

```json
{
  "action_id": "act_9821",
  "agent_id": "support_agent",
  "actor_role": "ai_agent",
  "tool": "issue_refund",
  "action": "issue_refund",
  "arguments": { "customer_id": "cust_193", "amount": 150, "currency": "USD" },
  "context": {
    "conversation_id": "conv_4821",
    "reason": "appointment cancellation",
    "previous_actions": []
  },
  "timestamp": "2026-09-21T11:32:00Z"
}
```

| Field | Meaning |
|---|---|
| `action_id` | Unique ID for this attempt. Decisions and approvals point back to it. |
| `agent_id` | Which agent made the call (`booking_agent`, `support_agent`). |
| `actor_role` | The role the agent acts under; matched against `Policy.subject.roles`. |
| `tool` | The MCP tool being invoked. |
| `action` | The semantic action. Often equals `tool`, but a generic tool (`send_message`) may carry a more specific action (`send_marketing_message`). |
| `arguments` | The raw tool-call payload — free-form per tool. This is where `conditions[].field` values are read from. |
| `context` | Optional situational metadata: conversation ID, the agent's stated reason, prior actions. Not used by the rule engine; feeds Stage A reasoning and makes flag cards compelling. |
| `timestamp` | Interception time; orders the `/actions` feed. |

### `decisions` — the gateway's verdict (one per action)

```json
{
  "decision": "requires_approval",
  "action_id": "act_9821",
  "policy_ids": ["refund_limit_001"],
  "reason": "Refund amount exceeds the $100 agent authorization limit.",
  "required_approval": "manager",
  "expires_at": "2026-09-21T20:00:00Z",
  "llm_reasoning": "The agent is attempting to refund $150 to cust_193 ...",
  "resolution": null
}
```

| Field | Meaning |
|---|---|
| `decision` | `allow` \| `block` \| `requires_approval`. Anything not `allow` becomes a flag in the UI. |
| `action_id` | The action being judged. |
| `policy_ids` | Which policies triggered the outcome — flag cards link to them. |
| `reason` | Human-readable explanation; the most important field for the UI. |
| `required_approval` | Copied from the winning policy's `approval_role`; only for `requires_approval`. |
| `expires_at` | Deadline after which a pending approval lapses (auto-reject). Drives the countdown on `/approvals`. |
| `llm_reasoning` | Stage A output (backend-only field): the LLM's narrative of what the agent was doing and which policies apply. Explainability only — never gates the decision. |
| `resolution` | Backend-only: `null` while pending, then `{ "by": "manager_priya", "outcome": "approved", "at": "..." }` once a human acts. Pending approvals = `decision: "requires_approval"` and `resolution: null`. |

## Frontend types ↔ collections

`frontend/src/lib/types.ts` mirrors the above:

- `Policy` + `PolicyCondition` ↔ `policies` collection
- `AgentAction` ↔ `actions` collection
- `GatewayDecision` ↔ `decisions` collection (minus backend-only fields
  `llm_reasoning` and `resolution`, which can be added to the type when the UI
  needs them)
- `Decision` (`"allow" | "block" | "requires_approval"`) and `PolicyCategory`
  are the shared enums used across all of them

Everything is intentionally loose (plain strings, `Record<string, unknown>` for
arguments) — no zod, no strict validation. This is a hackathon prototype; the
types exist so the UI and backend agree on shape, not to police it.
