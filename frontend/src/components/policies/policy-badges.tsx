import type { PolicyCategory, Policy } from "@/lib/types";

const categoryLabels: Record<PolicyCategory, string> = {
  payments: "Payments", customer_data: "Customer data", orders: "Orders", pricing: "Pricing", communication: "Communication", access_permissions: "Access permissions",
};

const categoryStyles: Record<PolicyCategory, string> = {
  payments: "bg-violet-50 text-violet-700", customer_data: "bg-sky-50 text-sky-700", orders: "bg-blue-50 text-blue-700", pricing: "bg-fuchsia-50 text-fuchsia-700", communication: "bg-teal-50 text-teal-700", access_permissions: "bg-orange-50 text-orange-700",
};

const statusStyles: Record<Policy["status"], string> = {
  active: "bg-emerald-50 text-emerald-700 ring-emerald-600/20", draft: "bg-slate-100 text-slate-700 ring-slate-500/20", pending_review: "bg-amber-50 text-amber-800 ring-amber-600/20",
};

const statusLabels: Record<Policy["status"], string> = { active: "Active", draft: "Draft", pending_review: "Awaiting review" };

export function PolicyCategoryBadge({ category }: { category: PolicyCategory }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold tracking-[-0.01em] ring-1 ring-inset ring-black/[0.035] ${categoryStyles[category]}`}>{categoryLabels[category]}</span>;
}

export function PolicyStatusBadge({ status }: { status: Policy["status"] }) {
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-[-0.01em] ring-1 ring-inset ${statusStyles[status]}`}><span className="size-1.5 rounded-full bg-current opacity-75" />{statusLabels[status]}</span>;
}
