"""MCP tool server for Maplewood Home & Living.

Each tool maps 1:1 to a business API endpoint and calls the same service
functions as the FastAPI router. These tools do not enforce policy.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import ValidationError

from .. import services
from ..models.models import (
    CancelRequest,
    CancelResponse,
    CreditApplication,
    CustomerLookupResponse,
    DiscountRequest,
    DiscountResponse,
    ExportRequest,
    ExportResponse,
    Order,
    OrderListResponse,
    PaymentMethod,
    RefundRequest,
    RefundResponse,
    ReturnRequest,
    ReturnResponse,
    ShippingAddressRequest,
)

mcp = FastMCP(
    "maplewood-tools",
    host="0.0.0.0",
    port=8001,
    streamable_http_path="/mcp",
)


@mcp.tool()
def get_customer_record(phone: str) -> CustomerLookupResponse:
    """Look up a customer by the phone they're chatting from. GET /customers."""
    try:
        customer = services.get_customer(phone)
    except services.NotFoundError as exc:
        raise ToolError(str(exc)) from exc
    return CustomerLookupResponse.model_validate(customer.model_dump())


@mcp.tool()
def get_order_status(order_id: str) -> Order:
    """Get order details. GET /orders/{order_id}."""
    try:
        return services.get_order(order_id)
    except services.NotFoundError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def get_orders(customer_id: str) -> OrderListResponse:
    """List every order for a customer. GET /customers/{customer_id}/orders."""
    try:
        return services.get_orders(customer_id)
    except services.NotFoundError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def issue_refund(
    order_id: str,
    customer_id: str,
    amount: float,
    reason: str,
    payment_method: PaymentMethod | None = None,
    currency: str = "USD",
) -> RefundResponse:
    """Issue a refund. POST /orders/{order_id}/refunds."""
    try:
        return services.issue_refund(
            order_id,
            RefundRequest(
                order_id=order_id,
                customer_id=customer_id,
                amount=amount,
                payment_method=payment_method,
                currency=currency,
                reason=reason,
            ),
        )
    except (services.NotFoundError, services.BadRequestError, ValidationError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def apply_discount(
    order_id: str,
    discount_percent: float,
    reason: str,
) -> DiscountResponse:
    """Apply a percent discount. POST /orders/{order_id}/discounts."""
    try:
        return services.apply_discount(
            order_id,
            DiscountRequest(
                order_id=order_id,
                discount_percent=discount_percent,
                reason=reason,
            ),
        )
    except (services.NotFoundError, services.BadRequestError, ValidationError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def get_credit_application(customer_id: str) -> CreditApplication:
    """Fetch a credit-account application. GET /customers/{id}/credit-application."""
    try:
        return services.get_credit_application(customer_id)
    except services.NotFoundError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def export_customer_list(destination: str, reason: str) -> ExportResponse:
    """Export every customer record. POST /customers/export."""
    try:
        return services.export_customers(
            ExportRequest(destination=destination, reason=reason)
        )
    except ValidationError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def update_shipping_address(
    order_id: str,
    street: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "US",
) -> Order:
    """Replace the shipping address. PUT /orders/{order_id}/shipping-address."""
    try:
        return services.update_shipping_address(
            order_id,
            ShippingAddressRequest(
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            ),
        )
    except (services.NotFoundError, ValidationError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def cancel_order(order_id: str, reason: str) -> CancelResponse:
    """Cancel an order. POST /orders/{order_id}/cancel."""
    try:
        return services.cancel_order(
            order_id, CancelRequest(order_id=order_id, reason=reason)
        )
    except (services.NotFoundError, services.BadRequestError, ValidationError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def return_order(order_id: str, reason: str) -> ReturnResponse:
    """Return a delivered order within 10 days of ordered_on and refund its full amount. POST /orders/{order_id}/return."""
    try:
        return services.return_order(
            order_id, ReturnRequest(order_id=order_id, reason=reason)
        )
    except (services.NotFoundError, services.BadRequestError, ValidationError) as exc:
        raise ToolError(str(exc)) from exc


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()