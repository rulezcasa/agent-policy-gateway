"use client";

import { ActionFeed } from "@/components/actions/action-feed";
import { StatCard } from "@/components/ui/stat-card";
import { getActions, getIngestionPolicies } from "@/lib/api";
import { useLiveResource } from "@/lib/use-live-resource";

export default function ActionsPage() {
  const snapshot = useLiveResource(async () => {
    const [actions, policies] = await Promise.all([getActions(), getIngestionPolicies()]);
    return { actions, policies };
  });
  const actions = snapshot.data?.actions ?? [];
  const policies = snapshot.data?.policies ?? [];
  const count = (decision: "allow" | "block" | "requires_approval") => actions.filter((item) => item.decision === decision).length;

  return <div className="space-y-8">
    <section><h2 className="text-2xl font-semibold tracking-tight text-slate-950">Agent actions</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">See each agent action and whether it was allowed, blocked, or is waiting for approval.</p></section>
    {snapshot.isLoading && !snapshot.data ? <p className="text-sm text-slate-600">Loading actions…</p> : snapshot.error && !snapshot.data ? <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800"><p>Could not load the action feed. {snapshot.error}</p><button type="button" onClick={() => void snapshot.refresh()} className="mt-3 rounded-lg bg-white px-3.5 py-2 font-semibold text-rose-800 ring-1 ring-inset ring-rose-200">Try again</button></div> : <>
      {snapshot.error && <p role="alert" className="text-sm text-rose-700">Latest refresh failed: {snapshot.error}</p>}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><StatCard label="Agent actions" value={actions.length} detail="Actions recorded so far" icon={<span>◷</span>} /><StatCard label="Allowed" value={count("allow")} detail="Allowed to proceed" tone="coral" icon={<span>✓</span>} /><StatCard label="Blocked" value={count("block")} detail="Stopped by policy" tone="rose" icon={<span>×</span>} /><StatCard label="Approval required" value={count("requires_approval")} detail="Waiting for a decision" tone="amber" icon={<span>!</span>} /></section>
      <section><div><h3 className="text-lg font-semibold text-slate-950">Action feed</h3></div><div className="mt-5"><ActionFeed actions={actions} policies={policies} /></div></section>
    </>}
  </div>;
}
