"use client";

import Link from "next/link";
import { useState } from "react";
import { RuleReviewCard, type ReviewStatus } from "@/components/policies/rule-review-card";
import { StatCard } from "@/components/ui/stat-card";
import { mockPolicies } from "@/lib/mock-data";
import type { Policy } from "@/lib/types";

const extractedRules = mockPolicies.filter((policy) => policy.status === "pending_review");

function ReviewIcon({ type }: { type: "all" | "pending" | "confirmed" | "rejected" }) {
  const symbol = { all: "≡", pending: "…", confirmed: "✓", rejected: "×" }[type];
  return <span className="text-lg font-semibold">{symbol}</span>;
}

export default function PolicyReviewPage() {
  const [rules, setRules] = useState<Policy[]>(extractedRules);
  const [statuses, setStatuses] = useState<Record<string, ReviewStatus>>(() => Object.fromEntries(extractedRules.map((policy) => [policy.policy_id, "pending"])));
  const pending = rules.filter((rule) => statuses[rule.policy_id] === "pending").length;
  const confirmed = rules.filter((rule) => statuses[rule.policy_id] === "confirmed").length;
  const rejected = rules.filter((rule) => statuses[rule.policy_id] === "rejected").length;

  function updateStatus(policyId: string, status: ReviewStatus) {
    setStatuses((current) => ({ ...current, [policyId]: status }));
    if (status === "confirmed") setRules((current) => current.map((policy) => policy.policy_id === policyId ? { ...policy, status: "active" } : policy));
  }

  function updateRule(updated: Policy) { setRules((current) => current.map((policy) => policy.policy_id === updated.policy_id ? updated : policy)); }

  return <div className="space-y-8"><section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h2 className="text-2xl font-semibold tracking-tight text-slate-950">Review extracted rules</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Confirm the structured rules produced from uploaded policy documents. Only administrator-confirmed rules become active for gateway enforcement.</p><p className="mt-2 font-mono text-xs text-slate-500">Source documents: 02_customer_data_handling_guidelines.pdf · 03_orders_shipping_and_communication_handbook.pdf</p></div><div className="flex flex-wrap gap-3"><Link href="/policies" className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Back to policies</Link><Link href="/policies/upload" className="rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Upload another policy</Link></div></section>
    <section aria-label="Review summary" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><StatCard label="Extracted rules" value={rules.length} detail="In this review session" icon={<ReviewIcon type="all" />} /><StatCard label="Awaiting review" value={pending} detail="Need administrator confirmation" tone="amber" icon={<ReviewIcon type="pending" />} /><StatCard label="Confirmed" value={confirmed} detail="Activated locally for this demo" tone="indigo" icon={<ReviewIcon type="confirmed" />} /><StatCard label="Rejected" value={rejected} detail="Not approved for enforcement" tone="rose" icon={<ReviewIcon type="rejected" />} /></section>
    <section><div className="mb-4 flex flex-col justify-between gap-2 sm:flex-row sm:items-end"><div><h3 className="text-lg font-semibold text-slate-950">Human-in-the-loop review</h3><p className="mt-1 text-sm text-slate-500">Compare the source wording with the canonical rule before deciding whether it should govern agent actions.</p></div>{pending === 0 && <Link href="/policies" className="text-sm font-semibold text-indigo-700 hover:text-indigo-800">Return to policies</Link>}</div><div className="space-y-5">{rules.map((rule) => <RuleReviewCard key={rule.policy_id} policy={rule} reviewStatus={statuses[rule.policy_id]} onStatusChange={(status) => updateStatus(rule.policy_id, status)} onEdit={updateRule} />)}</div></section>
  </div>;
}
