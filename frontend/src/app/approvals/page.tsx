"use client";

import { useState } from "react";
import { ApprovalQueue } from "@/components/actions/approval-queue";
import { StatCard } from "@/components/ui/stat-card";
import { getApprovals, getIngestionPolicies } from "@/lib/api";
import { useLiveResource } from "@/lib/use-live-resource";
import type { PendingTask } from "@/lib/types";

export default function ApprovalsPage() {
  const snapshot = useLiveResource(async () => {
    const [tasks, policies] = await Promise.all([getApprovals(), getIngestionPolicies()]);
    return { tasks, policies };
  });
  const [overrides, setOverrides] = useState<Record<string, PendingTask>>({});
  const tasks = (snapshot.data?.tasks ?? []).map((task) => overrides[task.action_id] ?? task);
  const policies = snapshot.data?.policies ?? [];
  const pending = tasks.filter((task) => task.status === "pending_approval" || task.status === "executing").length;
  const approved = tasks.filter((task) => task.status === "executed").length;
  const rejected = tasks.filter((task) => task.status === "rejected").length;

  return <div className="space-y-8">
    <section><h2 className="text-2xl font-semibold tracking-tight text-slate-950">Approvals</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Approve or reject agent actions that are waiting for a decision.</p></section>
    {snapshot.isLoading && !snapshot.data ? <p className="text-sm text-slate-600">Loading the approval queue…</p> : snapshot.error && !snapshot.data ? <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800"><p>Could not load approvals. {snapshot.error}</p><button type="button" onClick={() => void snapshot.refresh()} className="mt-3 rounded-lg bg-white px-3.5 py-2 font-semibold text-rose-800 ring-1 ring-inset ring-rose-200">Try again</button></div> : <>
      {snapshot.error && <p role="alert" className="text-sm text-rose-700">Latest refresh failed: {snapshot.error}</p>}
      <section className="grid gap-4 sm:grid-cols-3"><StatCard label="Pending approvals" value={pending} detail="Waiting for a decision" tone="amber" icon={<span>!</span>} /><StatCard label="Approved" value={approved} detail="Allowed to proceed" tone="coral" icon={<span>✓</span>} /><StatCard label="Rejected" value={rejected} detail="Not allowed to proceed" tone="rose" icon={<span>×</span>} /></section>
      <section><h3 className="text-lg font-semibold text-slate-950">Approval queue</h3><div className="mt-5"><ApprovalQueue tasks={tasks} policies={policies} onUpdated={(task) => setOverrides((current) => ({ ...current, [task.action_id]: task }))} /></div></section>
    </>}
  </div>;
}
