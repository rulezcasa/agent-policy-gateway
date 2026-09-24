import json
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from .. import services
from ..ingestion.pipeline import (
    POLICIES_PATH,
    UPLOADS_DIR,
    list_documents,
    process_documents,
    update_policy,
)
from ..policy_engine.store import read_actions, read_pending
from ..gateway.approvals import resolve_approval
from ..models.models import (
    ApprovalRequest,
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
    PolicyReviewRequest,
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



@router.post("/policies/upload", tags=["ingestion"])
async def upload_policies(files: list[UploadFile] = File(...)) -> list[dict]:
    paths = []
    for file in files:
        path = UPLOADS_DIR / file.filename
        path.write_bytes(await file.read())
        paths.append(path)
    return await process_documents(paths)


@router.get("/ingestion/policies", tags=["ingestion"])
def get_extracted_policies() -> list[dict]:
    return json.loads(POLICIES_PATH.read_text()) if POLICIES_PATH.exists() else []


@router.get("/ingestion/documents", tags=["ingestion"])
def get_extracted_documents() -> list[dict]:
    return list_documents()


@router.get("/actions", tags=["gateway"])
def list_actions() -> list[dict]:
    return list(reversed(read_actions()))


@router.get("/approvals", tags=["gateway"])
def list_approvals() -> list[dict]:
    return list(reversed(read_pending()))


@router.post("/approvals/{action_id}", tags=["gateway"])
async def decide_approval(action_id: str, request: ApprovalRequest) -> dict:
    try:
        return await resolve_approval(action_id, request.outcome, request.by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/ingestion/policies/{policy_id}", tags=["ingestion"])
def review_extracted_policy(policy_id: str, request: PolicyReviewRequest) -> dict:
    try:
        return update_policy(policy_id, request.model_dump(exclude_none=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


