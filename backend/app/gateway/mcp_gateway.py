"""MCP policy gateway. Same tool names as the business server, on port 8002."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .intercept import intercept

mcp = FastMCP(
    "maplewood-gateway",
    host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
    port=int(os.getenv("GATEWAY_PORT", "8002")),
    streamable_http_path="/mcp",
)


@mcp.tool()
async def get_customer_record(phone: str) -> str:
    """Look up a customer by the phone they're chatting from."""
    return await intercept("get_customer_record", {"phone": phone})


@mcp.tool()
async def get_order_status(order_id: str) -> str:
    """Get order details."""
    return await intercept("get_order_status", {"order_id": order_id})


@mcp.tool()
async def get_orders(customer_id: str) -> str:
    """List every order for a customer."""
    return await intercept("get_orders", {"customer_id": customer_id})


@mcp.tool()
async def issue_refund(
    order_id: str,
    customer_id: str,
    amount: float,
    reason: str,
    payment_method: str | None = None,
    currency: str = "USD",
) -> str:
    """Issue a refund."""
    return await intercept(
        "issue_refund",
        {
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount,
            "reason": reason,
            "payment_method": payment_method,
            "currency": currency,
        },
    )


@mcp.tool()
async def apply_discount(order_id: str, discount_percent: float, reason: str) -> str:
    """Apply a percent discount."""
    return await intercept(
        "apply_discount",
        {
            "order_id": order_id,
            "discount_percent": discount_percent,
            "reason": reason,
        },
    )


@mcp.tool()
async def get_credit_application(customer_id: str) -> str:
    """Fetch a credit-account application."""
    return await intercept("get_credit_application", {"customer_id": customer_id})


@mcp.tool()
async def export_customer_list(destination: str, reason: str) -> str:
    """Export every customer record."""
    return await intercept(
        "export_customer_list",
        {"destination": destination, "reason": reason},
    )


@mcp.tool()
async def update_shipping_address(
    order_id: str,
    street: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "US",
) -> str:
    """Replace the shipping address."""
    return await intercept(
        "update_shipping_address",
        {
            "order_id": order_id,
            "street": street,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
        },
    )


@mcp.tool()
async def cancel_order(order_id: str, reason: str) -> str:
    """Cancel an order."""
    return await intercept("cancel_order", {"order_id": order_id, "reason": reason})


@mcp.tool()
async def return_order(order_id: str, reason: str) -> str:
    """Return a delivered order and refund its full amount."""
    return await intercept("return_order", {"order_id": order_id, "reason": reason})


def main() -> None:
    mcp.run(transport="streamable-http")
