import type { ReactNode } from "react";

export function StatCard({ label, value, detail, tone = "slate", icon }: { label: string; value: number; detail: string; tone?: "slate" | "coral" | "rose" | "amber"; icon: ReactNode }) {
  const tones = { slate: "bg-slate-100 text-slate-700", coral: "bg-coral-50 text-coral-700", rose: "bg-rose-50 text-rose-700", amber: "bg-amber-50 text-amber-700" };
  return <section className="border-l border-slate-200/90 px-5 py-1 first:border-l-0 sm:px-6"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-medium uppercase tracking-[0.09em] text-slate-500">{label}</p><p className="mt-2 text-[31px] font-medium tracking-[-0.045em] text-slate-950 tabular-nums">{value}</p></div><span className={`flex size-8 items-center justify-center rounded-lg ring-1 ring-inset ring-black/[0.03] ${tones[tone]}`}>{icon}</span></div><p className="mt-2 text-[13px] leading-5 text-slate-500">{detail}</p></section>;
}
