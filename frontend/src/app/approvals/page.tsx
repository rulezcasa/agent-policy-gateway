// Flagged (non-compliant) actions awaiting human approval or rejection — the demo money shot.
"use client";

import { useCallback, useState } from "react";
import { ApprovalQueue } from "@/components/actions/approval-queue";
import { StatCard } from "@/components/ui/stat-card";
import { mockActions, mockDecisions, mockPolicies } from "@/lib/mock-data";

export default function ApprovalsPage() {
  const approvalDecisions = mockDecisions.filter((decision) => decision.decision === "requires_approval");
  const [counts, setCounts] = useState({ pending: approvalDecisions.length, approved: 0, rejected: 0 });
  const updateCounts = useCallback((next: typeof counts) => setCounts((current) => current.pending === next.pending && current.approved === next.approved && current.rejected === next.rejected ? current : next), []);
  return <div className="space-y-8"><section className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-2xl font-semibold tracking-tight text-slate-950">Approvals</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Agent actions held by the policy gateway while they wait for an authorized human decision. Approving or rejecting here changes local demo state only.</p></div><span className="inline-flex w-fit rounded-full bg-amber-50 px-3 py-1.5 text-sm font-semibold text-amber-800 ring-1 ring-inset ring-amber-600/20">Human decision required</span></section><section className="grid gap-4 sm:grid-cols-3"><StatCard label="Pending approvals" value={counts.pending} detail="Held by the gateway" tone="amber" icon={<span>!</span>} /><StatCard label="Approved" value={counts.approved} detail="Resolved locally in this demo" tone="indigo" icon={<span>✓</span>} /><StatCard label="Rejected" value={counts.rejected} detail="Not authorized to proceed" tone="rose" icon={<span>×</span>} /></section><section><h3 className="text-lg font-semibold text-slate-950">Human approval queue</h3><p className="mt-1 text-sm text-slate-500">Review why the rule engine held each action, then make the required administrator decision.</p><div className="mt-5"><ApprovalQueue actions={mockActions.filter((action) => approvalDecisions.some((decision) => decision.action_id === action.action_id))} decisions={approvalDecisions} policies={mockPolicies} onCountsChange={updateCounts} /></div></section></div>;
}
