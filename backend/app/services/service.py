from datetime import date, timedelta

from .. import db
from ..models.models import (
    CancelRequest,
    CancelResponse,
    ReturnRequest,
    ReturnResponse,
    CreditApplication,
    Customer,
    DiscountRequest,
    DiscountResponse,
    ExportRequest,
    ExportResponse,
    Order,
    OrderListResponse,
    RefundRequest,
    RefundResponse,
    ShippingAddress,
    ShippingAddressRequest,
)


class NotFoundError(LookupError):
    pass


class BadRequestError(ValueError):
    pass


RETURN_WINDOW_DAYS = 10


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


def get_orders(customer_id: str) -> OrderListResponse:
    orders = db.list_orders_for_customer(customer_id)
    if orders is None:
        raise NotFoundError(f"Customer {customer_id} was not found")
    return OrderListResponse(customer_id=customer_id, orders=orders)


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


def return_order(order_id: str, request: ReturnRequest) -> ReturnResponse:
    order = get_order(order_id)
    _require_matching_order_id(order_id, request.order_id)
    _require_open_return_window(order)
    updated = db.update_order_fulfillment_status(order_id, "returned")
    if updated is None:
        raise NotFoundError(f"Order {order_id} was not found")
    refund = issue_refund(
        order_id,
        RefundRequest(
            order_id=order_id,
            customer_id=order.customer_id,
            amount=order.amount,
            payment_method=order.payment_method,
            currency=order.currency,
            reason=request.reason,
        ),
    )
    return ReturnResponse(
        order_id=order_id,
        customer_id=order.customer_id,
        fulfillment_status="returned",
        amount=refund.amount,
        currency=refund.currency,
        payment_method=refund.payment_method,
        refund_id=refund.refund_id,
        reason=request.reason,
    )


def _require_open_return_window(order: Order) -> None:
    if order.fulfillment_status != "delivered":
        raise BadRequestError("Only a delivered order can be returned")
    age_days = (date.today() - order.ordered_on).days
    if age_days < 0 or age_days > RETURN_WINDOW_DAYS:
        raise BadRequestError(
            f"This order is outside the {RETURN_WINDOW_DAYS}-day return window"
        )


def _require_matching_order_id(path_id: str, body_id: str) -> None:
    if path_id != body_id:
        raise BadRequestError("Path and body order IDs must match")
