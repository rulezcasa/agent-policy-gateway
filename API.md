# Maplewood Business API

HTTP APIs for Maplewood Home & Living. These are the **business system** — they
do not enforce company policy. JSON in and out. No auth for the demo.

Eight endpoints. One per action in [AGENT_USECASE.md](AGENT_USECASE.md).

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
