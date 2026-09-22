"""MCP tool server for Maplewood Home & Living.

Each tool maps 1:1 to an endpoint in API.md. Demo records are in data.py.
These tools do not enforce policy — that is the gateway's job.
"""

from __future__ import annotations

import argparse
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.tools import data

mcp = MCPServer("maplewood-tools")


def _order(order_id: str) -> dict[str, Any]:
    order = data.orders.get(order_id)
    if order is None:
        raise ToolError(f"Order not found: {order_id}")
    return order


def _order_public(order: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **order}


@mcp.tool()
def get_customer_record(phone: str) -> dict[str, Any]:
    """Look up a customer by the phone they're chatting from. GET /customers."""
    customer = data.customer_by_phone(phone)
    if customer is None:
        raise ToolError(f"Customer not found for phone: {phone}")
    return {"ok": True, **customer}


@mcp.tool()
def get_order_status(order_id: str) -> dict[str, Any]:
    """Get order details. GET /orders/{order_id}."""
    return _order_public(_order(order_id))


@mcp.tool()
def issue_refund(
    order_id: str,
    customer_id: str,
    amount: float,
    payment_method: str | None = None,
    currency: str = "USD",
    reason: str = "",
) -> dict[str, Any]:
    """Issue a refund. POST /orders/{order_id}/refunds."""
    order = _order(order_id)
    method = payment_method or order["payment_method"]
    return {
        "ok": True,
        "refund_id": data.next_refund_id(order_id),
        "order_id": order_id,
        "customer_id": customer_id,
        "amount": amount,
        "payment_method": method,
        "currency": currency,
        "reason": reason,
    }


@mcp.tool()
def apply_discount(
    order_id: str,
    discount_percent: float,
    reason: str = "",
) -> dict[str, Any]:
    """Apply a percent discount. POST /orders/{order_id}/discounts."""
    order = _order(order_id)
    order["amount"] = round(order["amount"] * (1 - discount_percent / 100), 2)
    return {
        "ok": True,
        "order_id": order_id,
        "discount_percent": discount_percent,
        "amount": order["amount"],
        "reason": reason,
    }


@mcp.tool()
def get_credit_application(customer_id: str) -> dict[str, Any]:
    """Fetch a credit-account application. GET /customers/{id}/credit-application."""
    app = data.credit_apps.get(customer_id)
    if app is None:
        raise ToolError(f"No credit application for customer: {customer_id}")
    return {"ok": True, **app}


@mcp.tool()
def export_customer_list(
    destination: str = "external",
    reason: str = "",
) -> dict[str, Any]:
    """Export every customer record. POST /customers/export."""
    return {
        "ok": True,
        "export_id": data.next_export_id(),
        "destination": destination,
        "customer_count": len(data.customers),
        "reason": reason,
    }


@mcp.tool()
def update_shipping_address(
    order_id: str,
    street: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "US",
) -> dict[str, Any]:
    """Replace the shipping address. PUT /orders/{order_id}/shipping-address."""
    order = _order(order_id)
    order["shipping_address"] = {
        "street": street,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
    }
    return _order_public(order)


@mcp.tool()
def cancel_order(order_id: str, reason: str = "") -> dict[str, Any]:
    """Cancel an order. POST /orders/{order_id}/cancel."""
    order = _order(order_id)
    order["fulfillment_status"] = "cancelled"
    return {
        "ok": True,
        "order_id": order_id,
        "fulfillment_status": "cancelled",
        "reason": reason,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Maplewood MCP tool server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="streamable-http",
        help="stdio for a local subprocess; streamable-http for LangChain / Inspector",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
