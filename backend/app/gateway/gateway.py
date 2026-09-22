from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..engine.rules import evaluate
from ..models.gateway_models import (
    ActionRequest,
    AgentAction,
    ApprovalRequest,
    GatewayDecision,
    GatewayResult,
    Policy,
    Resolution,
)
from ..policies import POLICIES

router = APIRouter(prefix="/gateway", tags=["policy gateway"])

ACTIONS: dict[str, AgentAction] = {}
DECISIONS: dict[str, GatewayDecision] = {}


@router.post("/check", response_model=GatewayResult)
def check_action(request: ActionRequest) -> GatewayResult:
    result = evaluate(request)
    ACTIONS[result.action.action_id] = result.action
    DECISIONS[result.decision.action_id] = result.decision
    return result


@router.get("/actions", response_model=list[AgentAction])
def list_actions() -> list[AgentAction]:
    return sorted(ACTIONS.values(), key=lambda action: action.timestamp, reverse=True)


@router.get("/decisions", response_model=list[GatewayDecision])
def list_decisions() -> list[GatewayDecision]:
    return sorted(
        DECISIONS.values(), key=lambda decision: decision.action_id, reverse=True
    )


@router.get("/policies", response_model=list[Policy])
def list_policies() -> list[Policy]:
    return POLICIES


@router.get("/approvals", response_model=list[GatewayResult])
def list_approvals() -> list[GatewayResult]:
    results = []
    for action_id, decision in DECISIONS.items():
        if decision.decision != "requires_approval" or decision.resolution is not None:
            continue
        results.append(GatewayResult(action=ACTIONS[action_id], decision=decision))
    return results


@router.post("/approvals/{action_id}", response_model=GatewayResult)
def resolve_approval(action_id: str, request: ApprovalRequest) -> GatewayResult:
    action = ACTIONS.get(action_id)
    decision = DECISIONS.get(action_id)
    if action is None or decision is None:
        raise HTTPException(status_code=404, detail="Action was not found")
    if decision.decision != "requires_approval":
        raise HTTPException(status_code=400, detail="Action does not require approval")
    if decision.resolution is not None:
        raise HTTPException(status_code=409, detail="Approval was already resolved")

    decision.resolution = Resolution(
        by=request.by,
        outcome=request.outcome,
        at=datetime.now(timezone.utc),
    )
    return GatewayResult(action=action, decision=decision)
