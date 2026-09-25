"use client";

import { useMemo, useState } from "react";
import { DecisionBadge } from "./decision-badge";
import type { Decision, Policy, RecordedAction } from "@/lib/types";

const filters: { label: string; value: "all" | Decision }[] = [
  { label: "All", value: "all" },
  { label: "Allowed", value: "allow" },
  { label: "Blocked", value: "block" },
  { label: "Approval required", value: "requires_approval" },
];

const pretty = (value: string) => value.split("_").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");
const time = (value: string) => new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "UTC" }).format(new Date(value));

function explanation(action: RecordedAction) {
  return action.llm_reasoning || action.customer_message || "No explanation was recorded for this decision.";
}

function policyNames(action: RecordedAction, policies: Policy[]) {
  return action.policy_ids.map((id) => policies.find((policy) => policy.policy_id === id)?.name ?? id).join(", ");
}

function argumentChips(arguments_: Record<string, unknown>) {
  return Object.entries(arguments_).slice(0, 6).map(([key, value]) => (
    <span key={key} className="rounded-md bg-white px-2 py-1 font-mono text-xs text-slate-600 ring-1 ring-inset ring-slate-200">{key}: {typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
  ));
}

export function ActionFeed({ actions, policies }: { actions: RecordedAction[]; policies: Policy[] }) {
  const [filter, setFilter] = useState<"all" | Decision>("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const results = useMemo(() => actions.filter((action) => {
    const matchesFilter = filter === "all" || action.decision === filter;
    const searchable = `${action.agent_id} ${action.tool} ${action.action}`.toLowerCase();
    return matchesFilter && searchable.includes(query.toLowerCase());
  }), [actions, filter, query]);
  const selected = actions.find((action) => action.action_id === selectedId) ?? null;

  return <>
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap gap-2">{filters.map((item) => <button key={item.value} type="button" onClick={() => setFilter(item.value)} className={`h-9 rounded-full px-3.5 text-sm font-semibold ${filter === item.value ? "bg-coral-600 text-white shadow-sm shadow-coral-200" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-300 hover:bg-slate-50"}`}>{item.label}</button>)}</div>
      <label className="relative"><span className="sr-only">Search actions</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search agent or tool" className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3.5 text-sm outline-none placeholder:text-slate-400 focus:border-coral-500 sm:w-60" /></label>
    </div>
    {results.length === 0 ? <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center"><h3 className="font-semibold text-slate-900">No actions match this view</h3><p className="mt-2 text-sm text-slate-500">Agent actions will show up here.</p></div> : <div className="mt-5 space-y-3">{results.map((action) => <button type="button" onClick={() => setSelectedId(action.action_id)} key={action.action_id} className="w-full rounded-2xl border border-slate-200/90 bg-white p-5 text-left shadow-[0_1px_2px_rgba(15,23,42,0.025)] transition-all duration-150 hover:-translate-y-px hover:border-coral-200 hover:bg-coral-50/[0.3] hover:shadow-[0_8px_24px_rgba(15,23,42,0.05)]"><div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold tracking-[-0.015em] text-slate-950">{pretty(action.action || action.tool)}</h3><DecisionBadge decision={action.decision} /></div><p className="mt-1.5 text-sm text-slate-600"><span className="font-medium">{action.agent_id}</span> · {action.tool} · {time(action.timestamp)} UTC</p><p className="mt-2.5 text-sm leading-6 text-slate-600">{explanation(action)}</p>{action.policy_ids.length > 0 && <p className="mt-2.5 text-xs font-semibold text-coral-700">Policy: {policyNames(action, policies)}</p>}</div><span className="shrink-0 text-sm font-semibold text-coral-700">View details →</span></div></button>)}</div>}
    {selected && <div className="fixed inset-0 z-50 flex items-end bg-slate-950/35 p-0 sm:items-center sm:justify-center sm:p-6"><button aria-label="Close details" className="absolute inset-0" onClick={() => setSelectedId(null)} /><section role="dialog" aria-modal="true" aria-labelledby="action-detail-title" className="relative max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-6 shadow-2xl sm:max-w-2xl sm:rounded-2xl"><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-medium text-coral-700">Intercepted action</p><h2 id="action-detail-title" className="mt-1 text-xl font-semibold text-slate-950">{pretty(selected.action || selected.tool)}</h2></div><button type="button" onClick={() => setSelectedId(null)} className="rounded-lg px-2 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-100">Close</button></div><div className="mt-6 space-y-5"><div className="flex flex-wrap gap-2"><DecisionBadge decision={selected.decision} />{selected.required_approval && <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800">Requires {selected.required_approval.replaceAll("_", " ")}</span>}</div><dl className="grid gap-4 sm:grid-cols-2"><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Agent / role</dt><dd className="mt-1 text-sm text-slate-800">{selected.agent_id} · {selected.actor_role}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Tool / action</dt><dd className="mt-1 font-mono text-sm text-slate-800">{selected.tool} / {selected.action}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Timestamp</dt><dd className="mt-1 text-sm text-slate-800">{time(selected.timestamp)} UTC</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Relevant policies</dt><dd className="mt-1 text-sm text-slate-800">{selected.policy_ids.length ? policyNames(selected, policies) : "No linked policy"}</dd></div></dl><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Arguments</p>{selected.customer_message && <p className="mt-2 text-sm leading-6 text-slate-700">{selected.customer_message}</p>}<div className="mt-3 flex flex-wrap gap-2">{argumentChips(selected.arguments)}</div></div><div className="rounded-xl border border-coral-100 bg-coral-50/50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-coral-700">Policy evaluation</p><p className="mt-2 text-sm leading-6 text-slate-700">{explanation(selected)}</p><p className="mt-2 text-xs text-slate-500">The gateway made this enforcement decision. This page displays the recorded outcome.</p></div></div></section></div>}
  </>;
}
