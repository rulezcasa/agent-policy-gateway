from .. import db
from ..models.models import (
    CancelRequest,
    CancelResponse,
    CreditApplication,
    Customer,
    DiscountRequest,
    DiscountResponse,
    ExportRequest,
    ExportResponse,
    Order,
    RefundRequest,
    RefundResponse,
    ShippingAddress,
    ShippingAddressRequest,
)


class NotFoundError(LookupError):
    pass


class BadRequestError(ValueError):
    pass


def get_customer(phone: str) -> Customer:
    customer = db.get_customer_by_phone(phone)
    if customer is None:
        raise NotFoundError("Customer was not found")
    return customer


def get_order(order_id: str) -> Order:
    order = db.get_order(order_id)
    if order is None:
        raise NotFoundError(f"Order {order_id} was not found")
    return order


def issue_refund(order_id: str, request: RefundRequest) -> RefundResponse:
    order = get_order(order_id)
    _require_matching_order_id(order_id, request.order_id)
    return RefundResponse(
        refund_id=f"ref_{order_id.removeprefix('ORD-')}",
        order_id=order_id,
        customer_id=request.customer_id,
        amount=request.amount,
        payment_method=request.payment_method or order.payment_method,
        currency=request.currency,
        reason=request.reason,
    )


def apply_discount(order_id: str, request: DiscountRequest) -> DiscountResponse:
    order = get_order(order_id)
    _require_matching_order_id(order_id, request.order_id)
    discounted_amount = round(order.amount * (1 - request.discount_percent / 100), 2)
    updated = db.update_order_amount(order_id, discounted_amount)
    if updated is None:
        raise NotFoundError(f"Order {order_id} was not found")
    return DiscountResponse(
        order_id=order_id,
        discount_percent=request.discount_percent,
        amount=updated.amount,
        reason=request.reason,
    )


def get_credit_application(customer_id: str) -> CreditApplication:
    application = db.get_credit_application(customer_id)
    if application is None:
        raise NotFoundError("Credit application was not found")
    return application


def export_customers(request: ExportRequest) -> ExportResponse:
    return ExportResponse(
        export_id="exp_001",
        destination=request.destination,
        customer_count=db.customer_count(),
        reason=request.reason,
    )


def update_shipping_address(order_id: str, request: ShippingAddressRequest) -> Order:
    get_order(order_id)
    updated = db.update_order_shipping_address(
        order_id, ShippingAddress.model_validate(request.model_dump())
    )
    if updated is None:
        raise NotFoundError(f"Order {order_id} was not found")
    return updated


def cancel_order(order_id: str, request: CancelRequest) -> CancelResponse:
    get_order(order_id)
    _require_matching_order_id(order_id, request.order_id)
    updated = db.update_order_fulfillment_status(order_id, "cancelled")
    if updated is None:
        raise NotFoundError(f"Order {order_id} was not found")
    return CancelResponse(
        order_id=order_id,
        fulfillment_status="cancelled",
        reason=request.reason,
    )


def _require_matching_order_id(path_id: str, body_id: str) -> None:
    if path_id != body_id:
        raise BadRequestError("Path and body order IDs must match")
