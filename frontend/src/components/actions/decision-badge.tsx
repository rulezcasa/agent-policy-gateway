import type { Decision } from "@/lib/types";

const labels: Record<Decision, string> = { allow: "Allowed", block: "Blocked", requires_approval: "Approval required" };
const styles: Record<Decision, string> = {
  allow: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  block: "bg-rose-50 text-rose-700 ring-rose-600/20",
  requires_approval: "bg-amber-50 text-amber-800 ring-amber-600/20",
};

export function DecisionBadge({ decision }: { decision: Decision }) {
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[13px] font-semibold tracking-[-0.01em] ring-1 ring-inset ${styles[decision]}`}><span className="size-1.5 rounded-full bg-current opacity-75" />{labels[decision]}</span>;
}
