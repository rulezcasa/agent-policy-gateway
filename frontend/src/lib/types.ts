// Shared types mirroring the canonical formats from the design doc.
// Keep loose — this is a hackathon demo, not a validation exercise.

export type Decision = "allow" | "block" | "requires_approval";

export type PolicyCategory =
  | "payments"
  | "customer_data"
  | "orders"
  | "pricing"
  | "communication"
  | "access_permissions";

export interface PolicyCondition {
  field: string;
  operator: string;
  value: string | number | Array<string | number>;
  unit?: string;
}

export interface Policy {
  policy_id: string;
  name: string;
  category: string;
  subject: { roles: string[] };
  action: string;
  conditions: PolicyCondition[];
  decision: Decision;
  approval_role?: string | null;
  priority?: number;
  version: number;
  status: "active" | "inactive" | "draft" | "pending_review";
  source_doc?: string;
  original_text?: string;
  needs_review?: boolean;
}

// Rules returned by the ingestion API use model-generated category labels,
// rather than the curated categories used by the existing mock policy data.
export interface IngestionPolicy {
  policy_id: string;
  name: string;
  category: string;
  subject: { roles: string[] };
  action: string;
  conditions: PolicyCondition[];
  decision: Decision;
  approval_role?: string | null;
  version: number;
  status: "active" | "inactive" | "draft" | "pending_review";
  source_doc?: string;
  original_text?: string;
  needs_review?: boolean;
}

export type IngestionPolicyUpdate = Partial<
  Pick<
    IngestionPolicy,
    "status" | "name" | "category" | "action" | "conditions" | "decision" | "approval_role"
  >
>;

export interface GatewayTool {
  name: string;
  description: string;
  parameters: { properties?: Record<string, unknown> };
}

export interface AgentAction {
  action_id: string;
  agent_id: string;
  actor_role: string;
  tool: string;
  action: string;
  arguments: Record<string, unknown>;
  context?: {
    conversation_id?: string;
    reason?: string;
    previous_actions?: string[];
  };
  timestamp: string;
}

export interface GatewayDecision {
  decision: Decision;
  action_id: string;
  policy_ids: string[];
  reason: string;
  required_approval?: string;
  expires_at?: string;
}

// One row from GET /api/actions. The decision lives on the action record.
export interface RecordedAction {
  action_id: string;
  agent_id: string;
  actor_role: string;
  tool: string;
  action: string;
  arguments: Record<string, unknown>;
  normalized_arguments?: Record<string, unknown>;
  timestamp: string;
  decision: Decision;
  policy_ids: string[];
  required_approval?: string | null;
  llm_reasoning?: string | null;
  customer_message?: string | null;
}

export type ApprovalStatus = "pending_approval" | "executing" | "executed" | "rejected" | "blocked";

export interface ApprovalResolution {
  by: string;
  outcome: "approved" | "rejected";
  at: string;
}

export interface WorkflowSnapshot {
  phone?: string;
  active_agent?: string;
  user_message?: string;
  conversation_history?: unknown[];
}

// One row from GET /api/approvals. Holds and blocks share this shape.
export interface PendingTask {
  action_id: string;
  status: ApprovalStatus;
  agent_id?: string;
  actor_role?: string;
  tool: string;
  action?: string;
  arguments: Record<string, unknown>;
  normalized_arguments?: Record<string, unknown>;
  timestamp?: string;
  decision: Decision;
  policy_ids: string[];
  required_approval?: string | null;
  llm_reasoning?: string | null;
  customer_message?: string | null;
  workflow_state?: WorkflowSnapshot;
  tool_result?: unknown;
  resolution?: ApprovalResolution | null;
  created_at: string;
}
