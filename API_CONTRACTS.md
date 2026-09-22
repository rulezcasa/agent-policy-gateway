# Maplewood Business API

HTTP APIs for Maplewood Home & Living. These are the **business system** — they
do not enforce company policy. JSON in and out. No auth for the demo.

Eight endpoints. One per action in [AGENT_USECASE_NEW.md](AGENT_USECASE_NEW.md).

---

### `GET /customers`

Look up one customer by the phone they're chatting from. Returns `customer_id`
for later calls, plus name, email, and order history.

**Input**

```json
{ "phone": "555-0198" }
```

**Output**

```json
{
  "ok": true,
  "customer_id": "cust_201",
  "name": "Elena Vasquez",
  "phone": "555-0198",
  "email": "elena.vasquez@example.com",
  "order_ids": ["ORD-1488"]
}
```

---

### `GET /orders/{order_id}`

Order details: product, amount, payment method, fulfillment status, shipping address.

`payment_method` is `card` | `cash` | `gift_card`.
`fulfillment_status` is `processing` | `dispatched` | `delivered` | `cancelled`.

**Input**

```json
{ "order_id": "ORD-1704" }
```

**Output**

```json
{
  "ok": true,
  "order_id": "ORD-1704",
  "customer_id": "cust_118",
  "product": "Oak dining chairs (set of 2)",
  "amount": 240,
  "currency": "USD",
  "payment_method": "card",
  "fulfillment_status": "processing",
  "shipping_address": {
    "street": "12 Pine Rd",
    "city": "Portland",
    "state": "OR",
    "postal_code": "97202",
    "country": "US"
  }
}
```

---

### `POST /orders/{order_id}/refunds`

Issue a refund. `payment_method` defaults to the order's if omitted.

**Input**

```json
{
  "order_id": "ORD-1501",
  "customer_id": "cust_193",
  "amount": 150,
  "payment_method": "card",
  "currency": "USD",
  "reason": "defective coffee maker"
}
```

**Output**

```json
{
  "ok": true,
  "refund_id": "ref_1501",
  "order_id": "ORD-1501",
  "customer_id": "cust_193",
  "amount": 150,
  "payment_method": "card",
  "currency": "USD",
  "reason": "defective coffee maker"
}
```

---

### `POST /orders/{order_id}/discounts`

Apply a percent discount. `amount` in the output is the new order total.

**Input**

```json
{
  "order_id": "ORD-1488",
  "discount_percent": 25,
  "reason": "sorry discount"
}
```

**Output**

```json
{
  "ok": true,
  "order_id": "ORD-1488",
  "discount_percent": 25,
  "amount": 60,
  "reason": "sorry discount"
}
```

---

### `GET /customers/{customer_id}/credit-application`

Fetch the customer's store-credit application (ID documents and income).

**Input**

```json
{ "customer_id": "cust_193" }
```

**Output**

```json
{
  "ok": true,
  "customer_id": "cust_193",
  "application_id": "cred_193",
  "status": "under_review",
  "full_name": "James Okonkwo",
  "ssn_last4": "4412",
  "id_document_type": "drivers_license",
  "annual_income": 62000,
  "requested_limit": 1500
}
```

---

### `POST /customers/export`

Export every customer record to an external destination.

**Input**

```json
{
  "destination": "partner_campaign",
  "reason": "export list for partner"
}
```

**Output**

```json
{
  "ok": true,
  "export_id": "exp_001",
  "destination": "partner_campaign",
  "customer_count": 4,
  "reason": "export list for partner"
}
```

---

### `PUT /orders/{order_id}/shipping-address`

Replace the shipping address. `country` defaults to `US`.

**Input**

```json
{
  "order_id": "ORD-1704",
  "street": "88 Harbor St",
  "city": "Portland",
  "state": "OR",
  "postal_code": "97201",
  "country": "US"
}
```

**Output**

```json
{
  "ok": true,
  "order_id": "ORD-1704",
  "customer_id": "cust_118",
  "product": "Oak dining chairs (set of 2)",
  "amount": 240,
  "currency": "USD",
  "payment_method": "card",
  "fulfillment_status": "processing",
  "shipping_address": {
    "street": "88 Harbor St",
    "city": "Portland",
    "state": "OR",
    "postal_code": "97201",
    "country": "US"
  }
}
```

---

### `POST /orders/{order_id}/cancel`

Cancel an order.

**Input**

```json
{
  "order_id": "ORD-1690",
  "reason": "customer changed mind"
}
```

**Output**

```json
{
  "ok": true,
  "order_id": "ORD-1690",
  "fulfillment_status": "cancelled",
  "reason": "customer changed mind"
}
```

---

## Endpoint Understanding Guide

The backend exposes two layers:

```text
Agent -> Policy Gateway -> Business API
```

The **business API** performs Maplewood operations. It does not enforce policy.
The **policy gateway** evaluates an agent action and returns `allow`, `block`, or
`requires_approval` before the business operation is performed.

### Endpoint Summary

| Method | Endpoint | Layer | Purpose |
|---|---|---|---|
| `GET` | `/health` | system | Check that the backend is running |
| `GET` | `/customers` | business | Look up a customer by phone |
| `GET` | `/orders/{order_id}` | business | Retrieve order details |
| `POST` | `/orders/{order_id}/refunds` | business | Issue a refund |
| `POST` | `/orders/{order_id}/discounts` | business | Apply a percentage discount |
| `GET` | `/customers/{customer_id}/credit-application` | business | Retrieve a credit application |
| `POST` | `/customers/export` | business | Export customer records |
| `PUT` | `/orders/{order_id}/shipping-address` | business | Replace a shipping address |
| `POST` | `/orders/{order_id}/cancel` | business | Cancel an order |
| `POST` | `/gateway/check` | gateway | Evaluate an agent tool call |
| `GET` | `/gateway/actions` | gateway | List intercepted actions |
| `GET` | `/gateway/decisions` | gateway | List gateway decisions |
| `GET` | `/gateway/policies` | gateway | List active policies |
| `GET` | `/gateway/approvals` | gateway | List unresolved approvals |
| `POST` | `/gateway/approvals/{action_id}` | gateway | Approve or reject a pending action |

### System Endpoint

#### `GET /health`

Use this to confirm that the service is reachable.

Response:

```json
{
  "status": "ok"
}
```

### Business Endpoint Details

#### `GET /customers?phone={phone}`

Looks up a customer using the phone number supplied by the caller.

The response contains the customer ID, contact details, and order IDs that can
be used in later requests.

Returns `404` when the phone number is not in the demo data.

#### `GET /orders/{order_id}`

Retrieves the product, amount, payment method, fulfillment status, and shipping
address for an order.

The gateway uses this order information as context when checking actions such as
shipping-address updates and cancellations.

Returns `404` when the order does not exist.

#### `POST /orders/{order_id}/refunds`

Creates a refund response for an order. The request body includes the customer,
amount, currency, payment method, and reason. If `payment_method` is omitted, the
business API uses the payment method stored on the order.

The business API does not decide whether an AI agent is allowed to refund. The
agent must call `/gateway/check` first.

#### `POST /orders/{order_id}/discounts`

Applies a percentage discount and returns the updated order total.

The gateway blocks an AI-agent discount above `20%`. The business endpoint itself
is policy-neutral and will calculate the result if called directly.

#### `GET /customers/{customer_id}/credit-application`

Returns the customer's credit-account application data in the demo system.

This endpoint is intentionally sensitive. The gateway blocks `ai_agent` calls to
this action according to the customer-data policy.

#### `POST /customers/export`

Creates an export response containing the destination, reason, and number of
customers included.

The gateway blocks AI-agent customer-list exports.

#### `PUT /orders/{order_id}/shipping-address`

Replaces the complete shipping address for an order. `country` defaults to `US`.

The gateway allows the demo processing order and blocks address changes after an
order is dispatched.

#### `POST /orders/{order_id}/cancel`

Cancels an order and returns its new `cancelled` status.

The gateway blocks cancellation after courier handoff, represented by the
`dispatched` fulfillment status.

### Gateway Endpoint Details

#### `POST /gateway/check`

This is the main policy-enforcement endpoint. Agents send the intended tool call
before calling a business endpoint.

Request:

```json
{
  "agent_id": "refund_agent",
  "actor_role": "ai_agent",
  "tool": "issue_refund",
  "arguments": {
    "amount": 150,
    "payment_method": "card"
  },
  "context": {
    "reason": "defective coffee maker"
  }
}
```

The response contains both the canonical action and the gateway decision:

```json
{
  "action": {
    "action_id": "act_9821",
    "agent_id": "refund_agent",
    "actor_role": "ai_agent",
    "tool": "issue_refund",
    "action": "issue_refund",
    "arguments": {
      "amount": 150,
      "payment_method": "card"
    },
    "context": {
      "reason": "defective coffee maker"
    },
    "timestamp": "2026-09-22T10:00:00Z"
  },
  "decision": {
    "decision": "requires_approval",
    "action_id": "act_9821",
    "policy_ids": ["refund_manager_001"],
    "reason": "Refunds above $100 require shift manager approval.",
    "required_approval": "manager",
    "expires_at": "2026-09-22T18:00:00Z"
  }
}
```

If `action` is omitted from the request, the gateway uses the `tool` value as
the semantic action. If an `order_id` is present, the gateway adds the order's
stored `fulfillment_status` and `payment_method` while evaluating conditions.

#### `GET /gateway/actions`

Returns all action attempts received by `/gateway/check`, newest first. This is
the source for the dashboard's action feed.

#### `GET /gateway/decisions`

Returns the decision recorded for each checked action. Decisions include the
matched policy IDs, human-readable reason, approval role, expiry, and resolution
when applicable.

#### `GET /gateway/policies`

Returns the active demo policy catalog. Each policy includes its source document
and original text so the dashboard can link a decision back to the rule that
caused it.

#### `GET /gateway/approvals`

Returns decisions with:

```text
decision = requires_approval
resolution = null
```

These are the items displayed in the approval queue.

#### `POST /gateway/approvals/{action_id}`

Resolves a pending approval.

Request:

```json
{
  "by": "manager_priya",
  "outcome": "approved"
}
```

`outcome` must be either `approved` or `rejected`. The response adds a
`resolution` object to the decision. The current demo records the resolution but
does not yet forward the approved action to the business API.

### Recommended Request Flow

For an AI agent action, use this order:

1. Send the intended action to `POST /gateway/check`.
2. If the decision is `block`, stop and show the returned `reason`.
3. If the decision is `requires_approval`, wait for `POST /gateway/approvals/{action_id}`.
4. If the result is approved, or the original decision is `allow`, call the matching business endpoint.
5. Display the action and decision using `/gateway/actions` and `/gateway/decisions`.

The current implementation stores actions, decisions, policies, customers, and
orders in memory. Restarting the backend clears this demo state.
