from collections.abc import Callable
from typing import ParamSpec, TypeVar

from fastapi import APIRouter, HTTPException, Query

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
    RefundRequest,
    RefundResponse,
    ReturnRequest,
    ReturnResponse,
    ShippingAddressRequest,
)

P = ParamSpec("P")
T = TypeVar("T")

router = APIRouter(tags=["business system"])


def _call(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    try:
        return fn(*args, **kwargs)
    except services.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except services.BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/customers", response_model=CustomerLookupResponse)
def get_customer(phone: str = Query(min_length=1)) -> CustomerLookupResponse:
    customer = _call(services.get_customer, phone)
    return CustomerLookupResponse.model_validate(customer.model_dump())


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    return _call(services.get_order, order_id)


@router.get("/customers/{customer_id}/orders", response_model=OrderListResponse)
def get_orders(customer_id: str) -> OrderListResponse:
    return _call(services.get_orders, customer_id)


@router.post("/orders/{order_id}/refunds", response_model=RefundResponse)
def issue_refund(order_id: str, request: RefundRequest) -> RefundResponse:
    return _call(services.issue_refund, order_id, request)


@router.post("/orders/{order_id}/discounts", response_model=DiscountResponse)
def apply_discount(order_id: str, request: DiscountRequest) -> DiscountResponse:
    return _call(services.apply_discount, order_id, request)


@router.get("/customers/{customer_id}/credit-application", response_model=CreditApplication)
def get_credit_application(customer_id: str) -> CreditApplication:
    return _call(services.get_credit_application, customer_id)


@router.post("/customers/export", response_model=ExportResponse)
def export_customers(request: ExportRequest) -> ExportResponse:
    return _call(services.export_customers, request)


@router.put("/orders/{order_id}/shipping-address", response_model=Order)
def update_shipping_address(order_id: str, request: ShippingAddressRequest) -> Order:
    return _call(services.update_shipping_address, order_id, request)


@router.post("/orders/{order_id}/cancel", response_model=CancelResponse)
def cancel_order(order_id: str, request: CancelRequest) -> CancelResponse:
    return _call(services.cancel_order, order_id, request)










































@router.post("/orders/{order_id}/return", response_model=ReturnResponse)
def return_order(order_id: str, request: ReturnRequest) -> ReturnResponse:
    return _call(services.return_order, order_id, request)
