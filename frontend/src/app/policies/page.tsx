import Link from "next/link";
import { PolicyTable } from "@/components/policies/policy-table";
import { StatCard } from "@/components/ui/stat-card";
import { mockPolicies } from "@/lib/mock-data";

function OverviewIcon({ type }: { type: "active" | "review" | "category" }) {
  const paths = {
    active: <><path d="M12 3 4.5 6v5c0 4.7 3.2 8.6 7.5 10 4.3-1.4 7.5-5.3 7.5-10V6L12 3Z" /><path d="m8.5 12 2.3 2.3 4.7-4.7" /></>,
    review: <><path d="M5 4h10l4 4v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" /><path d="M14 4v4h4M8 15h8M8 11h5" /></>,
    category: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  };
  return <svg aria-hidden="true" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">{paths[type]}</svg>;
}

export default function PoliciesPage() {
  const activePolicies = mockPolicies.filter((policy) => policy.status === "active");
  const awaitingReview = mockPolicies.filter((policy) => policy.status === "pending_review");
  const categories = new Set(mockPolicies.map((policy) => policy.category));

  return <div className="space-y-8">
    <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h2 className="text-[30px] font-medium tracking-[-0.045em] text-slate-950">Policies</h2><p className="mt-3 max-w-2xl text-[15px] leading-7 text-slate-500">Structured company rules used by the gateway to evaluate intercepted agent actions. Only active policies are enforced.</p></div><Link href="/policies/upload" className="inline-flex h-11 items-center justify-center rounded-xl bg-indigo-600 px-5 text-[14px] font-medium text-white shadow-sm transition-colors hover:bg-indigo-700">Upload policy</Link></section>

    <section aria-label="Policy overview" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><StatCard label="Active policies" value={activePolicies.length} detail="Currently enforced by the gateway" tone="indigo" icon={<OverviewIcon type="active" />} /><StatCard label="Awaiting review" value={awaitingReview.length} detail="Extracted rules need administrator confirmation" tone="amber" icon={<OverviewIcon type="review" />} /><StatCard label="Policy categories" value={categories.size} detail="Represented in the current policy set" icon={<OverviewIcon type="category" />} /></section>

    <section><div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><h3 className="text-lg font-semibold text-slate-950">Structured policy rules</h3><p className="mt-1 text-sm text-slate-500">Each row is one canonical rule extracted from a source document.</p></div>{awaitingReview.length > 0 && <Link href="/policies/review" className="text-sm font-semibold text-indigo-700 hover:text-indigo-800">Review {awaitingReview.length} pending rule{awaitingReview.length === 1 ? "" : "s"}</Link>}</div><PolicyTable policies={mockPolicies} /></section>
  </div>;
}
