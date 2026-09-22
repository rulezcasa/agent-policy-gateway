from fastapi import APIRouter, HTTPException, Query, status

from ..data import CREDIT_APPLICATIONS, CUSTOMERS, ORDERS
from ..models.models import (
    ApiResponse,
    CancelRequest,
    CancelResponse,
    CreditApplication,
    CustomerLookupResponse,
    DiscountRequest,
    DiscountResponse,
    ExportRequest,
    ExportResponse,
    Order,
    RefundRequest,
    RefundResponse,
    ShippingAddressRequest,
)

router = APIRouter(tags=["business system"])


def get_order_or_404(order_id: str) -> Order:
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")
    return order


@router.get("/customers", response_model=CustomerLookupResponse)
def get_customer(phone: str = Query(min_length=1)) -> CustomerLookupResponse:
    customer = CUSTOMERS.get(phone)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer was not found")
    return CustomerLookupResponse.model_validate(customer.model_dump())


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    return get_order_or_404(order_id)


@router.post("/orders/{order_id}/refunds", response_model=RefundResponse)
def issue_refund(order_id: str, request: RefundRequest) -> RefundResponse:
    order = get_order_or_404(order_id)
    if request.order_id != order_id:
        raise HTTPException(status_code=400, detail="Path and body order IDs must match")

    return RefundResponse(
        refund_id=f"ref_{order_id.removeprefix('ORD-')}",
        order_id=order_id,
        customer_id=request.customer_id,
        amount=request.amount,
        payment_method=request.payment_method or order.payment_method,
        currency=request.currency,
        reason=request.reason,
    )


@router.post("/orders/{order_id}/discounts", response_model=DiscountResponse)
def apply_discount(order_id: str, request: DiscountRequest) -> DiscountResponse:
    order = get_order_or_404(order_id)
    if request.order_id != order_id:
        raise HTTPException(status_code=400, detail="Path and body order IDs must match")

    discounted_amount = round(order.amount * (1 - request.discount_percent / 100), 2)
    order.amount = discounted_amount
    return DiscountResponse(
        order_id=order_id,
        discount_percent=request.discount_percent,
        amount=discounted_amount,
        reason=request.reason,
    )


@router.get("/customers/{customer_id}/credit-application", response_model=CreditApplication)
def get_credit_application(customer_id: str) -> CreditApplication:
    application = CREDIT_APPLICATIONS.get(customer_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Credit application was not found")
    return CreditApplication(customer_id=customer_id, **application)


@router.post("/customers/export", response_model=ExportResponse)
def export_customers(request: ExportRequest) -> ExportResponse:
    return ExportResponse(
        export_id="exp_001",
        destination=request.destination,
        customer_count=len(CUSTOMERS),
        reason=request.reason,
    )


@router.put("/orders/{order_id}/shipping-address", response_model=Order)
def update_shipping_address(
    order_id: str, request: ShippingAddressRequest
) -> Order:
    order = get_order_or_404(order_id)
    order.shipping_address = request
    return order


@router.post("/orders/{order_id}/cancel", response_model=CancelResponse)
def cancel_order(order_id: str, request: CancelRequest) -> CancelResponse:
    order = get_order_or_404(order_id)
    if request.order_id != order_id:
        raise HTTPException(status_code=400, detail="Path and body order IDs must match")

    order.fulfillment_status = "cancelled"
    return CancelResponse(
        order_id=order_id,
        fulfillment_status="cancelled",
        reason=request.reason,
    )
