"use client";

import Link from "next/link";
import { PolicyTable } from "@/components/policies/policy-table";
import { StatCard } from "@/components/ui/stat-card";
import { getIngestionPolicies, updateIngestionPolicy } from "@/lib/api";
import { useLiveResource } from "@/lib/use-live-resource";

function OverviewIcon({ type }: { type: "active" | "review" }) {
  const paths = {
    active: <><path d="M12 3 4.5 6v5c0 4.7 3.2 8.6 7.5 10 4.3-1.4 7.5-5.3 7.5-10V6L12 3Z" /><path d="m8.5 12 2.3 2.3 4.7-4.7" /></>,
    review: <><path d="M5 4h10l4 4v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" /><path d="M14 4v4h4M8 15h8M8 11h5" /></>,
  };
  return <svg aria-hidden="true" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">{paths[type]}</svg>;
}

export default function PoliciesPage() {
  const snapshot = useLiveResource(() => getIngestionPolicies());
  const policies = snapshot.data ?? [];
  const activePolicies = policies.filter((policy) => policy.status === "active");
  const awaitingReview = policies.filter((policy) => policy.status === "pending_review");

  return <div className="space-y-8">
    <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h2 className="text-[30px] font-medium tracking-[-0.045em] text-slate-950">Policies</h2><p className="mt-3 max-w-2xl text-[15px] leading-7 text-slate-500">Only active policies are enforced.</p></div><Link href="/policies/upload" className="inline-flex h-11 items-center justify-center rounded-xl bg-coral-600 px-5 text-[14px] font-medium text-white shadow-sm transition-colors hover:bg-coral-700">Upload policy</Link></section>
    {snapshot.isLoading && !snapshot.data ? <p className="text-sm text-slate-600">Loading policies…</p> : snapshot.error && !snapshot.data ? <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800"><p>Could not load policies. {snapshot.error}</p><button type="button" onClick={() => void snapshot.refresh()} className="mt-3 rounded-lg bg-white px-3.5 py-2 font-semibold text-rose-800 ring-1 ring-inset ring-rose-200">Try again</button></div> : <>
      {snapshot.error && <p role="alert" className="text-sm text-rose-700">Latest refresh failed: {snapshot.error}</p>}
      <section aria-label="Policy overview" className="grid gap-4 sm:grid-cols-2"><StatCard label="Active policies" value={activePolicies.length} detail="Currently enforced by the gateway" tone="coral" icon={<OverviewIcon type="active" />} /><StatCard label="Awaiting review" value={awaitingReview.length} detail="Extracted rules need administrator confirmation" tone="amber" icon={<OverviewIcon type="review" />} /></section>
      <section><div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><h3 className="text-lg font-semibold text-slate-950">Policy rules</h3></div>{awaitingReview.length > 0 && <Link href="/policies/review" className="text-sm font-semibold text-coral-700 hover:text-coral-800">Review {awaitingReview.length} rule{awaitingReview.length === 1 ? "" : "s"}</Link>}</div><PolicyTable policies={policies} onStatusChange={async (policyId, status) => { await updateIngestionPolicy(policyId, { status }); await snapshot.refresh(); }} /></section>
    </>}
  </div>;
}
