# Data Models

What we store, where, and what every field means. The files under
`backend/app/db/` are the records the gateway writes. `frontend/src/lib/types.ts`
is the earlier shared shape and does not yet list every field below.

## Storage: JSON files under `backend/app/db/`

The canonical policy format is nested JSON with variable shape: `conditions` is an
array of heterogeneous tests, `subject` is a nested object, and different policies
carry different optional fields (`approval_role`, `priority`, ...). Actions carry a
free-form `arguments` payload that differs per tool. The demo stores each of these
as a JSON file, read on every gateway call, so a review that flips `status` to
`active` applies without a restart. The chat, the gateway, and the API are
separate processes, so writes take a file lock.


| File                   | Holds                                                               |
| ---------------------- | ------------------------------------------------------------------- |
| `documents/doc_*.json` | One uploaded policy file and its extracted text                     |
| `categories.json`      | Category names proposed at ingestion                                |
| `policies.json`        | Canonical rules. Only `status: "active"` is enforced                |
| `actions.json`         | Every intercepted tool call, including allows                       |
| `pending_tasks.json`   | Blocks and holds. A hold is the approval queue and the resume token |
| `workflow_state.json`  | Live chat snapshot (phone, agent, history) copied onto a hold       |




## `policies` — one object per rule

```json
{
  "policy_id": "refund_limit_001",
  "name": "Refund authorization limit",
  "category": "payments",
  "subject": { "roles": ["ai_assistant", "support_staff"] },
  "action": "issue_refund",
  "conditions": [
    { "field": "amount", "operator": ">", "value": 100, "unit": "USD" }
  ],
  "decision": "requires_approval",
  "approval_role": "manager",
  "priority": 50,
  "version": 1,
  "status": "active",
  "source_doc": "doc_001",
  "original_text": "Anything above $100 needs sign-off from a shift manager...",
  "needs_review": false
}
```


| Field           | Meaning                                                                                                                                              |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `policy_id`     | Unique ID. Actions and pending tasks reference it.                                                                                                   |
| `name`          | Human-readable title shown in the UI.                                                                                                                |
| `category`      | Label assigned at ingestion. Used for filtering, not for enforcement.                                                                                |
| `subject.roles` | Who the rule binds. Matched against the caller role `ai_agent`. `ai_assistant`, `AI Assistant`, and `automated_assistant` are aliases of `ai_agent`. |
| `action`        | Tool this rule governs (`issue_refund`). `*` matches every tool.                                                                                     |
| `conditions`    | All must hold for the rule to trigger. Empty array means the rule always applies to this action.                                                     |
| `decision`      | `allow`, `block`, or `requires_approval` when the rule triggers.                                                                                     |
| `approval_role` | Who can approve. Copied to `required_approval` only when this rule wins and its decision is `requires_approval`.                                     |
| `priority`      | Highest number wins when several rules match. Missing priority is `0`. Equal priority breaks toward `block`, then `requires_approval`, then `allow`. |
| `version`       | Incremented when an admin edits the rule.                                                                                                            |
| `status`        | `pending_review` (extracted) → `active` (enforced) or `draft`. Extraction always writes `pending_review`.                                            |
| `source_doc`    | Document this rule came from.                                                                                                                        |
| `original_text` | Sentence the rule was extracted from. Shown on review. The ownership block uses this as the customer sentence.                                       |
| `needs_review`  | True when extraction could not ground the action or a condition field.                                                                               |




### `conditions[]`


| Field      | Meaning                                                                                 |
| ---------- | --------------------------------------------------------------------------------------- |
| `field`    | Key of the normalized arguments (`amount`, `discount_percent`, `order_owner_mismatch`). |
| `operator` | `>`, `>=`, `<`, `<=`, `==`, `!=`, `in`.                                                 |
| `value`    | Threshold or expected value.                                                            |
| `unit`     | Optional display unit: `USD`, `percent`.                                                |


Before comparison, a call with `order_id` is enriched with `fulfillment_status`, `payment_method`, `ordered_on`, and the order's `amount` when the tool call omitted them. It also sets `order_customer_id`, `caller_customer_id` (from the chat phone), and `order_owner_mismatch`. Those enriched fields are what the rules see. The original tool arguments are what a later approve forwards.

## `actions.json` — one object per intercepted call

Written for allows, blocks, and holds.

```json
{
  "action_id": "act_9821",
  "agent_id": "order_agent",
  "actor_role": "ai_agent",
  "tool": "issue_refund",
  "action": "issue_refund",
  "arguments": { "order_id": "ORD-1501", "customer_id": "cust_193", "amount": 150, "reason": "defective coffee maker" },
  "normalized_arguments": { "amount": 150, "payment_method": "card", "order_owner_mismatch": false },
  "timestamp": "2026-09-23T17:12:08+00:00",
  "decision": "requires_approval",
  "policy_ids": ["refund_amount_limit_standard_approval_10f2d7"],
  "required_approval": "manager",
  "llm_reasoning": "The refund is $150, which is over the $100 limit.",
  "customer_message": null
}
```


| Field                  | Meaning                                                                            |
| ---------------------- | ---------------------------------------------------------------------------------- |
| `action_id`            | This attempt. Approvals point back to it.                                          |
| `agent_id`             | `order_agent` or `support_agent`, from the workflow snapshot.                      |
| `actor_role`           | Always `ai_agent` for this demo.                                                   |
| `tool`                 | MCP tool name.                                                                     |
| `action`               | Same as `tool`. The normalizer does not rename it.                                 |
| `arguments`            | Original tool payload. This is what approve forwards.                              |
| `normalized_arguments` | Payload the rules compared, including order enrichment.                            |
| `timestamp`            | Interception time.                                                                 |
| `decision`             | `allow`, `block`, or `requires_approval`.                                          |
| `policy_ids`           | Rules that matched, winner first. Empty when nothing matched.                      |
| `required_approval`    | Winning policy's `approval_role`, or null.                                         |
| `llm_reasoning`        | Explanation for a block or a hold. Null on allow.                                  |
| `customer_message`     | Fixed sentence the dummy chat prints. Set for the ownership block; otherwise null. |




## `pending_tasks.json` — blocks and holds

Same fields as the action, plus the resume state. A hold is `decision: "requires_approval"` and `status: "pending_approval"`.

```json
{
  "action_id": "act_9821",
  "status": "pending_approval",
  "tool": "issue_refund",
  "arguments": { "order_id": "ORD-1501", "amount": 150 },
  "normalized_arguments": { "amount": 150, "payment_method": "card" },
  "decision": "requires_approval",
  "policy_ids": ["refund_amount_limit_standard_approval_10f2d7"],
  "required_approval": "manager",
  "llm_reasoning": "The refund is $150, which is over the $100 limit.",
  "customer_message": null,
  "workflow_state": {
    "phone": "555-0142",
    "active_agent": "order_agent",
    "user_message": "Refund $150 for the coffee maker",
    "conversation_history": []
  },
  "tool_result": null,
  "resolution": null,
  "created_at": "2026-09-23T17:12:08+00:00"
}
```


| Field            | Meaning                                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `status`         | `pending_approval` → `executing` → `executed`, or `pending_approval` → `rejected`. A block stays `blocked` and is never forwarded. |
| `workflow_state` | Copy of `workflow_state.json` at intercept time: phone, agent, user message, history.                                              |
| `tool_result`    | Tool-server response after approve. Null until then.                                                                               |
| `resolution`     | Null while pending, then `{ "by", "outcome", "at" }`. `outcome` is `approved` or `rejected`.                                       |
| `created_at`     | Used by the dummy chat to find the hold from this turn.                                                                            |


`executing` is the lock that stops a double approve from issuing two refunds. If the tool server fails, status returns to `pending_approval.`

## `workflow_state.json`

One object, overwritten at the start of each chat turn and again after the reply is saved. The gateway reads it to learn the phone and which agent is active.

`conversation_history` stores what the customer was shown. When a tool call is blocked or held, the next entry has `role: "policy"` and the reason, so the following turn can explain it without retrying the call.

## Frontend

`/actions` reads `GET /api/actions`. `/approvals` reads `GET /api/approvals` and posts `POST /api/approvals/{action_id}`. `frontend/src/lib/types.ts` is the earlier shared shape; the JSON files above are what the backend writes today.