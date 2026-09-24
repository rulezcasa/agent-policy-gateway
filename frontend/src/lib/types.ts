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
  value: string | number;
  unit?: string;
}

export interface Policy {
  policy_id: string;
  name: string;
  category: PolicyCategory;
  subject: { roles: string[] };
  action: string;
  conditions: PolicyCondition[];
  decision: Decision;
  approval_role?: string;
  version: number;
  status: "active" | "draft" | "pending_review";
  source_doc?: string; // original uploaded file
  original_text?: string; // the raw policy fragment this rule was extracted from
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
