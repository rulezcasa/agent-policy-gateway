"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getIngestionPolicies, getIngestionTools, updateIngestionPolicy } from "@/lib/api";
import type { GatewayTool, IngestionPolicy, IngestionPolicyUpdate } from "@/lib/types";
import { ConnectedRuleReviewCard } from "./connected-rule-review-card";
import { StatCard } from "@/components/ui/stat-card";

function ReviewIcon({ type }: { type: "all" | "pending" | "confirmed" | "draft" }) {
  const symbol = { all: "≡", pending: "…", confirmed: "✓", draft: "—" }[type];
  return <span className="text-lg font-semibold">{symbol}</span>;
}

export function ConnectedPolicyReviewPage() {
  const [rules, setRules] = useState<IngestionPolicy[]>([]);
  const [tools, setTools] = useState<GatewayTool[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadRules = useCallback(async () => {
    setIsLoading(true); setLoadError(null);
    try {
      const [loadedRules, loadedTools] = await Promise.all([getIngestionPolicies(), getIngestionTools().catch(() => [] as GatewayTool[])]);
      setRules(loadedRules);
      setTools(loadedTools);
    } catch (error) { setLoadError(error instanceof Error ? error.message : "Unable to load the review queue."); } finally { setIsLoading(false); }
  }, []);

  useEffect(() => {
    void Promise.all([getIngestionPolicies(), getIngestionTools().catch(() => [] as GatewayTool[])])
      .then(([loadedRules, loadedTools]) => { setRules(loadedRules); setTools(loadedTools); })
      .catch((error: unknown) => setLoadError(error instanceof Error ? error.message : "Unable to load the review queue."))
      .finally(() => setIsLoading(false));
  }, []);

  async function saveRule(policyId: string, update: IngestionPolicyUpdate) {
    const updated = await updateIngestionPolicy(policyId, update);
    const actionIsMapped = update.action != null && tools.some((tool) => tool.name === update.action);
    setRules((current) => current.map((policy) => policy.policy_id === policyId ? { ...policy, ...updated, ...update, needs_review: actionIsMapped ? false : (updated.needs_review ?? policy.needs_review) } : policy));
  }

  const pendingRules = rules.filter((rule) => rule.status === "pending_review");
  const visibleRules = pendingRules;
  const active = rules.filter((rule) => rule.status === "active").length;
  const draft = rules.filter((rule) => rule.status === "draft").length;

  return <div className="space-y-8"><section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h2 className="text-2xl font-semibold tracking-tight text-slate-950">Review extracted rules</h2></div><div className="flex flex-wrap gap-3"><Link href="/policies" className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Back to policies</Link><Link href="/policies/upload" className="rounded-lg bg-coral-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-coral-700">Upload another policy</Link></div></section>
    <section aria-label="Review summary" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><StatCard label="Saved rules" value={rules.length} detail="Loaded from the review queue" icon={<ReviewIcon type="all" />} /><StatCard label="Awaiting review" value={pendingRules.length} detail="Need administrator confirmation" tone="amber" icon={<ReviewIcon type="pending" />} /><StatCard label="Active" value={active} detail="Ready for gateway enforcement" tone="coral" icon={<ReviewIcon type="confirmed" />} /><StatCard label="Parked" value={draft} detail="Set aside, still available to confirm" tone="rose" icon={<ReviewIcon type="draft" />} /></section>
    <section><div className="mb-4 flex flex-col justify-between gap-2 sm:flex-row sm:items-end"><div><h3 className="text-lg font-semibold text-slate-950">Rules</h3></div>{pendingRules.length === 0 && !isLoading && <Link href="/policies" className="text-sm font-semibold text-coral-700 hover:text-coral-800">Return to policies</Link>}</div>{isLoading ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-600">Loading the review queue...</div> : loadError ? <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800"><p>{loadError}</p><button type="button" onClick={() => void loadRules()} className="mt-3 rounded-lg bg-white px-3.5 py-2 font-semibold text-rose-800 ring-1 ring-inset ring-rose-200 hover:bg-rose-100">Try again</button></div> : visibleRules.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-600">There are no rules awaiting review.</div> : <div className="space-y-5">{visibleRules.map((rule) => <ConnectedRuleReviewCard key={`${rule.policy_id}-${rule.status}-${rule.action}-${rule.needs_review}`} policy={rule} tools={tools} onConfirm={() => saveRule(rule.policy_id, { status: "active" })} onPark={() => saveRule(rule.policy_id, { status: "draft" })} onDeactivate={() => saveRule(rule.policy_id, { status: "inactive" })} onEdit={(update) => saveRule(rule.policy_id, update)} />)}</div>}</section>
  </div>;
}
