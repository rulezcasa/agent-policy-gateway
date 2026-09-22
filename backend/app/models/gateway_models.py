from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Decision = Literal["allow", "block", "requires_approval"]
PolicyCategory = Literal[
    "payments",
    "customer_data",
    "orders",
    "pricing",
]


class PolicyCondition(BaseModel):
    field: str
    operator: Literal[">", ">=", "<", "<=", "==", "!=", "in"]
    value: str | int | float | list[str]
    unit: str | None = None


class PolicySubject(BaseModel):
    roles: list[str]


class Policy(BaseModel):
    policy_id: str
    name: str
    category: PolicyCategory
    subject: PolicySubject
    action: str
    conditions: list[PolicyCondition] = Field(default_factory=list)
    decision: Decision
    approval_role: str | None = None
    priority: int
    version: int = 1
    status: Literal["active", "draft", "pending_review"] = "active"
    source_doc: str
    original_text: str


class AgentAction(BaseModel):
    action_id: str
    agent_id: str
    actor_role: str
    tool: str
    action: str
    arguments: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class ActionRequest(BaseModel):
    agent_id: str
    actor_role: str = "ai_agent"
    tool: str
    action: str | None = None
    arguments: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)


class Resolution(BaseModel):
    by: str
    outcome: Literal["approved", "rejected"]
    at: datetime


class GatewayDecision(BaseModel):
    decision: Decision
    action_id: str
    policy_ids: list[str]
    reason: str
    required_approval: str | None = None
    expires_at: datetime | None = None
    llm_reasoning: str | None = None
    resolution: Resolution | None = None


class GatewayResult(BaseModel):
    action: AgentAction
    decision: GatewayDecision


class ApprovalRequest(BaseModel):
    by: str = Field(min_length=1)
    outcome: Literal["approved", "rejected"]
