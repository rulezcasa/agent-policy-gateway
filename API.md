# API Documentation

HTTP APIs for Maplewood Home & Living. Every route below is mounted under `/api` (for example `GET /api/customers`).

Two groups:

- **Business system** — CRUD operations on refunds, orders, customer data exposed via tools on an MCP server running on port 8001.
- **Gateway and ingestion** — Policy upload and review, the intercepted-action feed, and approve/reject. Routes requests via proxy MCP gateway running on port 8002.

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
  "order_ids": ["ORD-1488", "ORD-1602"]
}
```

---



### `GET /customers/{customer_id}/orders`

Every order for one customer, in `order_id` order. Unknown `customer_id` is 404.
A known customer with no orders returns an empty `orders` array.

**Input**

```json
{ "customer_id": "cust_201" }
```

**Output**

```json
{
  "ok": true,
  "customer_id": "cust_201",
  "orders": [
    {
      "ok": true,
      "order_id": "ORD-1488",
      "customer_id": "cust_201",
      "product": "Table lamp",
      "amount": 80,
      "currency": "USD",
      "payment_method": "card",
      "fulfillment_status": "processing",
      "ordered_on": "2026-09-20",
      "shipping_address": {
        "street": "44 Cedar Ave",
        "city": "Portland",
        "state": "OR",
        "postal_code": "97205",
        "country": "US"
      }
    }
  ]
}
```

---



### `GET /orders/{order_id}`

Order details: product, amount, payment method, fulfillment status, order date, shipping address.

`payment_method` is `card` | `cash` | `gift_card`.
`fulfillment_status` is `processing` | `dispatched` | `delivered` | `cancelled` | `returned`.
`ordered_on` is the date the order was placed, `YYYY-MM-DD`. A return is allowed only while this date is within the last 10 days.

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
  "ordered_on": "2026-09-21",
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
  "ordered_on": "2026-09-21",
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



### `POST /orders/{order_id}/return`

Return a delivered order and refund its full amount. The amount is taken from the order, not from the request. Sets `fulfillment_status` to `returned`.

The order must already be `delivered`, and `ordered_on` must be within the last 10 days. Otherwise the call is `400`. An order that is still `processing` or `dispatched`, or that was placed more than 10 days ago, is not returned.

**Input**

```json
{
  "order_id": "ORD-1602",
  "reason": "returned linen throw"
}
```

**Output**

```json
{
  "ok": true,
  "order_id": "ORD-1602",
  "customer_id": "cust_201",
  "fulfillment_status": "returned",
  "amount": 45,
  "currency": "USD",
  "payment_method": "card",
  "refund_id": "ref_1602",
  "reason": "returned linen throw"
}
```

---



## Gateway

These routes read and resolve what the MCP gateway already decided. They do not re-run policy checks. `GET` responses are newest first.

### `GET /actions`

Every intercepted tool call, including allows. Shape: an action record in [DATA_MODELS.md](DATA_MODELS.md).

### `GET /approvals`

Block and hold records. Pending rows have `status: "pending_approval"`. Shape: a pending task in [DATA_MODELS.md](DATA_MODELS.md).

### `POST /approvals/{action_id}`

Approve or reject a held call. Approve forwards the saved `arguments` to the tool server once and sets `status` to `executed`. A second approve returns the same row and does not forward again. Reject sets `status` to `rejected` and does not forward. Unknown `action_id` is 404. A tool-server failure is 502 and the row stays `pending_approval`.

**Input**

```json
{ "outcome": "approved", "by": "manager" }
```

`outcome` is `approved` or `rejected`.

**Output**

The updated pending-task record, including `tool_result` when approved and `resolution`.

---



## Ingestion



### `POST /policies/upload`

Upload one or more policy PDFs (`multipart` file field `files`). Runs extraction and appends rules with `status: "pending_review"`. Returns the new rule dicts.

### `GET /ingestion/policies`

Every rule in `policies.json`.

### `GET /ingestion/documents`

Uploaded documents and their extracted text.

### `PATCH /ingestion/policies/{policy_id}`

Confirm, edit, or park one extracted rule. Unknown `policy_id` is 404. Omitted fields are left unchanged.

**Input**

```json
{
  "status": "active",
  "decision": "requires_approval",
  "approval_role": "manager"
}
```

`status` is `active`, `draft`, or `pending_review`. 
`decision` is `allow`, `block`, or `requires_approval`. 
Only `active` rules are enforced. 
Optional fields: `name`, `category`, `action`, `conditions`.

**Output**
The updated policy.