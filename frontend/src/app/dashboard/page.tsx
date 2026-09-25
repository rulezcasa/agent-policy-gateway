"use client";

import Link from "next/link";
import { DecisionBadge } from "@/components/actions/decision-badge";
import { StatCard } from "@/components/ui/stat-card";
import { getActions, getApprovals, getIngestionPolicies } from "@/lib/api";
import { useLiveResource } from "@/lib/use-live-resource";
import type { PendingTask, RecordedAction } from "@/lib/types";

const titleForAction = (action: string) => action.split("_").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");
const formatTime = (timestamp: string) => new Intl.DateTimeFormat("en", { hour: "numeric", minute: "2-digit", timeZone: "UTC" }).format(new Date(timestamp));

function MetricIcon({ type }: { type: "policy" | "actions" | "block" | "approval" }) {
  const paths = { policy: <><path d="M7 3.5h7l3 3V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-15a1.5 1.5 0 0 1 1-1.5Z" /><path d="M14 3.5V7h3M9 12h6" /></>, actions: <><path d="M12 3a9 9 0 1 0 9 9" /><path d="M12 7v5l3 2M17 3v4h4" /></>, block: <><path d="M12 9v4m0 4h.01M10.3 3.9 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" /></>, approval: <><path d="M12 3 4.5 6v5c0 4.7 3.2 8.6 7.5 10 4.3-1.4 7.5-5.3 7.5-10V6L12 3Z" /><path d="m8.5 12 2.3 2.3 4.7-4.7" /></> };
  return <svg aria-hidden="true" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">{paths[type]}</svg>;
}

function explanation(action: RecordedAction) {
  return action.llm_reasoning || action.customer_message || "No explanation was recorded.";
}

export default function DashboardPage() {
  const snapshot = useLiveResource(async () => {
    const [policies, actions, approvals] = await Promise.all([getIngestionPolicies(), getActions(), getApprovals()]);
    return { policies, actions, approvals };
  });

  if (snapshot.isLoading && !snapshot.data) {
    return <p className="text-sm text-slate-600">Loading the gateway…</p>;
  }
  if (snapshot.error && !snapshot.data) {
    return <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800"><p>The dashboard could not reach the gateway. {snapshot.error}</p><button type="button" onClick={() => void snapshot.refresh()} className="mt-3 rounded-lg bg-white px-3.5 py-2 font-semibold text-rose-800 ring-1 ring-inset ring-rose-200 hover:bg-rose-100">Try again</button></div>;
  }

  const policies = snapshot.data?.policies ?? [];
  const actions = snapshot.data?.actions ?? [];
  const approvals: PendingTask[] = snapshot.data?.approvals ?? [];
  const recentActions = actions.slice(0, 5);
  const activePolicies = policies.filter((policy) => policy.status === "active");
  const inactivePolicies = policies.filter((policy) => policy.status === "inactive");
  const parkedPolicies = policies.filter((policy) => policy.status === "draft");
  const awaitingReview = policies.filter((policy) => policy.status === "pending_review");
  const policyDetail = [
    `${inactivePolicies.length} inactive`,
    `${parkedPolicies.length} parked`,
    awaitingReview.length > 0 ? `${awaitingReview.length} awaiting review` : null,
  ].filter(Boolean).join(" · ");
  const blockedActions = actions.filter((action) => action.decision === "block");
  const pendingApprovals = approvals.filter((task) => task.status === "pending_approval");
  const flags = actions.filter((action) => action.decision !== "allow").slice(0, 3);
  const categoryCount = new Set(activePolicies.map((policy) => policy.category)).size;
  const activeShare = policies.length === 0 ? 0 : (activePolicies.length / policies.length) * 100;

  return <div className="space-y-10">
    <section className="border-b border-slate-200/80 pb-8"><p className="text-xs font-medium uppercase tracking-[0.1em] text-coral-600">Maplewood Home & Living</p><h2 className="mt-3 text-[clamp(30px,3vw,36px)] font-medium tracking-[-0.05em] text-slate-950">Policies and recent actions</h2><p className="mt-3 max-w-2xl text-[15px] leading-7 text-slate-500">See which policies are in force, and which recent agent actions were allowed, blocked, or are waiting for a decision.</p></section>
    {snapshot.error && <p role="alert" className="text-sm text-rose-700">Latest refresh failed: {snapshot.error}</p>}
    <section aria-label="Overview" className="grid divide-y divide-slate-200/90 border-y border-slate-200/90 py-6 sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4"><StatCard label="Active policies" value={activePolicies.length} detail={policyDetail} tone="coral" icon={<MetricIcon type="policy" />} /><StatCard label="Intercepted actions" value={actions.length} detail="All tool calls observed" icon={<MetricIcon type="actions" />} /><StatCard label="Blocked actions" value={blockedActions.length} detail="Violations prevented" tone="rose" icon={<MetricIcon type="block" />} /><StatCard label="Pending approvals" value={pendingApprovals.length} detail="Human decisions needed" tone="amber" icon={<MetricIcon type="approval" />} /></section>

    <section className="grid gap-10 xl:grid-cols-[minmax(0,1fr)_280px]"><div><div className="flex items-end justify-between border-b border-slate-200/80 pb-4"><div><p className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">Live activity</p><h3 className="mt-2 text-[18px] font-medium tracking-[-0.025em] text-slate-950">Recent intercepted actions</h3></div><Link href="/actions" className="text-[14px] font-medium text-coral-700 hover:text-coral-800">View feed</Link></div>{recentActions.length === 0 ? <p className="py-8 text-sm text-slate-500">No intercepted tool calls yet.</p> : <div className="divide-y divide-slate-100">{recentActions.map((action) => <div key={action.action_id} className="grid gap-2 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2.5"><p className="text-[15px] font-medium text-slate-900">{titleForAction(action.action || action.tool)}</p><DecisionBadge decision={action.decision} /></div><p className="mt-1.5 truncate text-[14px] text-slate-500"><span className="font-medium text-slate-700">{action.agent_id}</span><span className="mx-1.5 text-slate-300">/</span>{action.tool}<span className="mx-1.5 text-slate-300">/</span>{explanation(action)}</p></div><time className="text-[13px] font-medium tabular-nums text-slate-400">{formatTime(action.timestamp)} UTC</time></div>)}</div>}</div>
      <aside className="border-l border-slate-200/80 pl-0 xl:pl-7"><p className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">Coverage</p><h3 className="mt-2 text-lg font-medium tracking-[-0.025em] text-slate-950">Enforcement readiness</h3><p className="mt-2 text-sm leading-6 text-slate-500">{categoryCount} categories represented by active rules.</p><div className="mt-7"><div className="flex items-baseline justify-between"><span className="text-sm text-slate-600">Policies active</span><span className="text-sm font-medium tabular-nums text-slate-900">{activePolicies.length}/{policies.length}</span></div><div className="mt-3 h-px bg-slate-200"><div className="h-px bg-coral-600" style={{ width: `${activeShare}%` }} /></div></div></aside>
    </section>

    <section className="border-t border-slate-200/80 pt-8"><div className="flex items-end justify-between"><div><p className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">Priority queue</p><h3 className="mt-2 text-lg font-medium tracking-[-0.025em] text-slate-950">Needs attention</h3></div><Link href="/approvals" className="text-sm font-medium text-coral-700 hover:text-coral-800">Review approvals</Link></div>{flags.length === 0 ? <p className="mt-4 text-sm text-slate-500">No blocked or held actions yet.</p> : <div className="mt-4 divide-y divide-slate-100">{flags.map((action) => <div key={action.action_id} className="py-4"><div className="flex flex-wrap items-center gap-2.5"><p className="text-sm font-medium text-slate-900">{titleForAction(action.action || action.tool)}</p><DecisionBadge decision={action.decision} /></div><p className="mt-2 text-sm leading-6 text-slate-500">{explanation(action)}</p>{action.required_approval && <p className="mt-2 text-xs font-medium capitalize text-amber-700">Required approver: {action.required_approval.replaceAll("_", " ")}</p>}</div>)}</div>}</section>
  </div>;
}
