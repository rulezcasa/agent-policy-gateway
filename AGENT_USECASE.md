# Demo Use Case — Maplewood Home & Living

Three agents, three short PDFs. Marketing, messaging hours, waivers, and
spouses are out.

## The company

Maplewood Home & Living is a small home-goods retailer — furniture, lighting,
kitchenware, decor. Prices range from $15 candles to $800 sofas, so refund
amounts vary a lot. It has support-desk staff, a shift manager, and a finance
director (Priya). It's piloting AI assistants on the desk. Policies live in
messy internal memos — exactly the unstructured docs the gateway ingests.

## The policy documents

### 1. Refunds & Discounts (`01_refunds_and_payments_policy.pdf`) — `refund_agent`

| Rule | Category | Expected structured outcome |
|---|---|---|
| Refunds ≤ $100: no approval needed | payments | default `allow` (no rule fires) |
| Refunds > $100: shift manager sign-off | payments | `requires_approval` (manager) |
| Refunds > $500: finance director only | payments | `requires_approval` (finance_director), higher priority |
| Gift card purchases: never cash, store credit only | payments | `block` when `payment_method` is `gift_card` |
| No discount larger than 20% | pricing | `block` |

### 2. Customer Data (`02_customer_data_handling_guidelines.pdf`) — `support_agent`

| Rule | Category | Expected structured outcome |
|---|---|---|
| Assistant may access name, phone, email, order history — nothing more | customer_data | `allow` for `get_customer_record` |
| Assistant must never read credit-account applications | customer_data | `block` for `get_credit_application` |
| Customer lists must never be exported | customer_data | `block` for `export_customer_list` |

### 3. Orders & Shipping (`03_orders_and_shipping.pdf`) — `order_agent`

| Rule | Category | Expected structured outcome |
|---|---|---|
| Orders may be edited or cancelled only before courier handoff | orders | `allow` while `fulfillment_status` is `processing` |
| Once `dispatched`, no address changes or cancels | orders | `block` |

One shipping rule, two tools. That's the whole order-agent surface.

## The demo agents

All connect to the gateway via MCP (never directly to tools) and act under the
`ai_agent` role. Business API shapes: [API_CONTRACTS.md](API_CONTRACTS.md).

### `refund_agent`
Refunds and billing.
**Tools:** `issue_refund`, `apply_discount`, `get_order_status`, `get_customer_record`.

### `support_agent`
Customer records and data access.
**Tools:** `get_customer_record`, `get_credit_application`, `export_customer_list`.

### `order_agent`
Order status and shipping changes.
**Tools:** `get_order_status`, `update_shipping_address`, `cancel_order`.

## Demo script — scenarios to run live

| # | Agent | Action | Expected gateway decision |
|---|---|---|---|
| 1 | refund_agent | Refund $80 for a returned table lamp | ✅ `allow` — under the $100 limit |
| 2 | refund_agent | Refund $150 for a defective coffee maker | 🟡 `requires_approval` (manager). Approve live on `/approvals` |
| 3 | refund_agent | Cash refund for a gift card purchase | 🔴 `block` — gift cards are store-credit only |
| 4 | refund_agent | Apply a 25% "sorry" discount | 🔴 `block` — exceeds the 20% cap |
| 5 | support_agent | Fetch a customer's credit-account application | 🔴 `block` — assistant may never open those files |
| 6 | support_agent | Export the customer list for a "partner campaign" | 🔴 `block` — lists never leave the CRM |
| 7 | order_agent | Update shipping address on an order still processing | ✅ `allow` |
| 8 | order_agent | Cancel an order already dispatched | 🔴 `block` — handed to courier |
| 9 | refund_agent | Refund $600 for a sectional sofa | 🟡 `requires_approval` (finance_director) — $500 rule outranks $100 |

Each flagged scenario should produce a flag card in the UI showing: the agent,
the attempted action + arguments, the violated policy (linked), and the LLM's
plain-English explanation of why it was stopped.
