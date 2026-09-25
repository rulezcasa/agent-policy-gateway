import type { Decision, PolicyCategory, Policy } from "@/lib/types";

const categoryLabels: Record<PolicyCategory, string> = {
  payments: "Payments", customer_data: "Customer data", orders: "Orders", pricing: "Pricing", communication: "Communication", access_permissions: "Access permissions",
};

const statusStyles: Record<Exclude<Policy["status"], "pending_review">, string> = {
  active: "bg-emerald-50 text-emerald-700 ring-emerald-600/20", inactive: "bg-red-50 text-red-700 ring-red-600/20", draft: "bg-slate-100 text-slate-700 ring-slate-500/20",
};

const statusLabels: Record<Policy["status"], string> = { active: "Active", inactive: "Inactive", draft: "Parked", pending_review: "Awaiting review" };

const enforcementLabels: Record<Decision, string> = { allow: "Allowed", block: "Blocking", requires_approval: "Approval" };

export function categoryLabel(category: PolicyCategory | string) {
  return categoryLabels[category as PolicyCategory] ?? category.replaceAll("_", " ");
}

export function enforcementTypeLabel(decision: Decision) {
  return enforcementLabels[decision];
}

export function PolicyCategoryBadge({ category }: { category: PolicyCategory | string }) {
  return <span className="text-sm text-slate-700">{categoryLabel(category)}</span>;
}

export function PolicyStatusBadge({ status }: { status: Policy["status"] }) {
  if (status === "pending_review") return <span className="text-sm text-slate-600">{statusLabels[status]}</span>;
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-[-0.01em] ring-1 ring-inset ${statusStyles[status]}`}><span className="size-1.5 rounded-full bg-current opacity-75" />{statusLabels[status]}</span>;
}
