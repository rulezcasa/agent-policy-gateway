from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PaymentMethod = Literal["card", "cash", "gift_card"]
FulfillmentStatus = Literal["processing", "dispatched", "delivered", "cancelled", "returned"]


class ApiResponse(BaseModel):
    ok: bool = True


class ShippingAddress(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"


class Customer(BaseModel):
    customer_id: str
    name: str
    phone: str
    email: str
    order_ids: list[str]


class CustomerLookupResponse(ApiResponse, Customer):
    pass


class Order(ApiResponse):
    order_id: str
    customer_id: str
    product: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    payment_method: PaymentMethod
    fulfillment_status: FulfillmentStatus
    ordered_on: date
    shipping_address: ShippingAddress


class OrderListResponse(ApiResponse):
    customer_id: str
    orders: list[Order]


class RefundRequest(BaseModel):
    order_id: str
    customer_id: str
    amount: float = Field(gt=0)
    payment_method: PaymentMethod | None = None
    currency: str = "USD"
    reason: str = Field(min_length=1)


class RefundResponse(ApiResponse):
    refund_id: str
    order_id: str
    customer_id: str
    amount: float
    payment_method: PaymentMethod
    currency: str
    reason: str


class DiscountRequest(BaseModel):
    order_id: str
    discount_percent: float = Field(gt=0, le=100)
    reason: str = Field(min_length=1)


class DiscountResponse(ApiResponse):
    order_id: str
    discount_percent: float
    amount: float
    reason: str


class CreditApplication(ApiResponse):
    customer_id: str
    application_id: str
    status: str
    full_name: str
    ssn_last4: str
    id_document_type: str
    annual_income: float
    requested_limit: float


class ExportRequest(BaseModel):
    destination: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class ExportResponse(ApiResponse):
    export_id: str
    destination: str
    customer_count: int
    reason: str


class ShippingAddressRequest(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"


class CancelRequest(BaseModel):
    order_id: str
    reason: str = Field(min_length=1)


class CancelResponse(ApiResponse):
    order_id: str
    fulfillment_status: Literal["cancelled"]
    reason: str


class ReturnRequest(BaseModel):
    order_id: str
    reason: str = Field(min_length=1)


class ReturnResponse(ApiResponse):
    order_id: str
    customer_id: str
    fulfillment_status: Literal["returned"]
    amount: float
    currency: str
    payment_method: PaymentMethod
    refund_id: str
    reason: str


class ApprovalRequest(BaseModel):
    outcome: Literal["approved", "rejected"]
    by: str = Field(min_length=1)


class PolicyReviewRequest(BaseModel):
    status: Literal["active", "draft", "pending_review"] | None = None
    name: str | None = None
    category: str | None = None
    action: str | None = None
    conditions: list[dict] | None = None
    decision: Literal["allow", "block", "requires_approval"] | None = None
    approval_role: str | None = None


class ModelConfigMixin:
    model_config = ConfigDict(extra="forbid")
