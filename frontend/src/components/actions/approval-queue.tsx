"use client";

import { useState } from "react";
import { decideApproval } from "@/lib/api";
import { DecisionBadge } from "./decision-badge";
import type { PendingTask, Policy } from "@/lib/types";

type QueueFilter = "all" | "pending" | "approved" | "rejected" | "blocked";

const pretty = (value: string) => value.split("_").map((word) => (word ? word[0].toUpperCase() + word.slice(1) : word)).join(" ");
const time = (value: string) => new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "UTC" }).format(new Date(value));

function queueStatus(task: PendingTask): Exclude<QueueFilter, "all"> {
  if (task.status === "executed") return "approved";
  if (task.status === "rejected") return "rejected";
  if (task.status === "blocked") return "blocked";
  return "pending";
}

const statusStyle: Record<Exclude<QueueFilter, "all">, string> = {
  pending: "bg-amber-50 text-amber-800 ring-amber-600/20",
  approved: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  rejected: "bg-rose-50 text-rose-700 ring-rose-600/20",
  blocked: "bg-rose-50 text-rose-700 ring-rose-600/20",
};

const statusLabel: Record<Exclude<QueueFilter, "all">, string> = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
  blocked: "Blocked",
};

function reason(task: PendingTask) {
  return task.llm_reasoning || task.customer_message || "The gateway recorded this decision without an explanation.";
}

function names(task: PendingTask, policies: Policy[]) {
  return task.policy_ids.map((id) => policies.find((policy) => policy.policy_id === id)?.name ?? id).join(", ");
}

function agentLabel(task: PendingTask) {
  return task.agent_id || task.workflow_state?.active_agent || "ai_agent";
}

export function ApprovalQueue({ tasks, policies, onUpdated }: { tasks: PendingTask[]; policies: Policy[]; onUpdated: (task: PendingTask) => void }) {
  const [filter, setFilter] = useState<QueueFilter>("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const items = tasks.filter((task) => {
    const status = queueStatus(task);
    const policyText = names(task, policies);
    const searchable = `${agentLabel(task)} ${task.action ?? ""} ${task.tool} ${policyText}`.toLowerCase();
    return (filter === "all" || status === filter) && searchable.includes(query.toLowerCase());
  });

  async function resolve(actionId: string, outcome: "approved" | "rejected") {
    setBusyId(actionId);
    setError(null);
    try {
      onUpdated(await decideApproval(actionId, outcome));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The gateway could not record this decision.");
    } finally {
      setBusyId(null);
    }
  }

  const selected = tasks.find((task) => task.action_id === selectedId) ?? null;

  return <>
    <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
      <div className="flex flex-wrap gap-2">{(["all", "pending", "approved", "rejected", "blocked"] as const).map((item) => <button key={item} type="button" onClick={() => setFilter(item)} className={`h-9 rounded-full px-3.5 text-sm font-semibold ${filter === item ? "bg-coral-600 text-white shadow-sm shadow-coral-200" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-300 hover:bg-slate-50"}`}>{item === "all" ? "All" : statusLabel[item]}</button>)}</div>
      <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search action, agent, or policy" className="h-10 rounded-xl border border-slate-300 bg-white px-3.5 text-sm outline-none focus:border-coral-500 sm:w-64" />
    </div>
    {error && <p role="alert" className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
    {items.length === 0 ? <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center"><h3 className="font-semibold text-slate-900">No approvals match this view</h3><p className="mt-2 text-sm text-slate-500">Actions waiting for a decision will show up here.</p></div> : <div className="mt-5 space-y-4">{items.map((task) => {
      const status = queueStatus(task);
      const canDecide = task.status === "pending_approval" && busyId !== task.action_id;
      return <article key={task.action_id} className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.025),0_8px_24px_rgba(15,23,42,0.025)]"><div className="flex flex-col gap-4 lg:flex-row lg:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="text-lg font-semibold tracking-[-0.02em] text-slate-950">{pretty(task.action || task.tool)}</h3><DecisionBadge decision={task.decision} /><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${statusStyle[status]}`}>{statusLabel[status]}</span></div><p className="mt-2 text-sm text-slate-600"><span className="font-medium">{agentLabel(task)}</span>{task.actor_role ? ` · ${task.actor_role}` : ""} · {time(task.created_at)} UTC</p><p className="mt-3 text-sm leading-6 text-slate-700">{reason(task)}</p><div className="mt-3 grid gap-2 text-sm sm:grid-cols-2"><p><span className="text-slate-500">Required approver: </span><span className="font-medium capitalize text-slate-800">{task.required_approval?.replaceAll("_", " ") || "—"}</span></p><p className="truncate"><span className="text-slate-500">Policy: </span><span className="font-medium text-coral-700">{names(task, policies) || "No linked policy"}</span></p></div>{task.resolution && <p className="mt-2 text-xs text-slate-500">{statusLabel[status]} by {task.resolution.by} · {time(task.resolution.at)} UTC</p>}</div><div className="flex shrink-0 flex-wrap items-start gap-2"><button type="button" onClick={() => setSelectedId(task.action_id)} className="h-10 rounded-xl border border-slate-300 px-3.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">View details</button>{canDecide && <><button type="button" onClick={() => void resolve(task.action_id, "approved")} className="h-10 rounded-xl bg-emerald-600 px-3.5 text-sm font-semibold text-white shadow-sm shadow-emerald-100 hover:bg-emerald-700">Approve</button><button type="button" onClick={() => void resolve(task.action_id, "rejected")} className="h-10 rounded-xl px-3.5 text-sm font-semibold text-rose-700 hover:bg-rose-50">Reject</button></>}</div></div></article>;
    })}</div>}
    {selected && (() => {
      const status = queueStatus(selected);
      const canDecide = selected.status === "pending_approval" && busyId !== selected.action_id;
      return <div className="fixed inset-0 z-50 flex items-end bg-slate-950/45 p-0 backdrop-blur-[2px] sm:items-center sm:justify-center sm:p-6"><button aria-label="Close details" className="absolute inset-0" onClick={() => setSelectedId(null)} /><section role="dialog" aria-modal="true" className="relative max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-6 shadow-2xl sm:max-w-2xl sm:rounded-2xl"><div className="flex justify-between"><div><p className="text-sm font-medium text-coral-700">Gateway-held action</p><h2 className="mt-1 text-xl font-semibold tracking-[-0.02em] text-slate-950">{pretty(selected.action || selected.tool)}</h2></div><button type="button" onClick={() => setSelectedId(null)} className="rounded-lg px-2 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-100">Close</button></div><div className="mt-5 flex gap-2"><DecisionBadge decision={selected.decision} /><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${statusStyle[status]}`}>{statusLabel[status]}</span></div><dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">Agent / role</dt><dd className="mt-1 text-slate-800">{agentLabel(selected)}{selected.actor_role ? ` · ${selected.actor_role}` : ""}</dd></div><div><dt className="text-slate-500">Tool / action</dt><dd className="mt-1 font-mono text-slate-800">{selected.tool} / {selected.action || selected.tool}</dd></div><div><dt className="text-slate-500">Required approver</dt><dd className="mt-1 capitalize text-slate-800">{selected.required_approval?.replaceAll("_", " ") || "—"}</dd></div><div><dt className="text-slate-500">Relevant policy</dt><dd className="mt-1 text-slate-800">{names(selected, policies) || "No linked policy"}</dd></div>{selected.workflow_state?.user_message && <div className="sm:col-span-2"><dt className="text-slate-500">Customer message</dt><dd className="mt-1 text-slate-800">{selected.workflow_state.user_message}</dd></div>}</dl><div className="mt-5 rounded-xl bg-slate-50 p-4"><p className="text-sm leading-6 text-slate-700">{reason(selected)}</p><div className="mt-3 flex flex-wrap gap-2">{Object.entries(selected.arguments).slice(0, 6).map(([key, value]) => <span key={key} className="rounded-md bg-white px-2 py-1 font-mono text-xs text-slate-600 ring-1 ring-inset ring-slate-200">{key}: {typeof value === "object" ? JSON.stringify(value) : String(value)}</span>)}</div></div>{selected.tool_result != null && <div className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4 text-sm text-emerald-900">Tool result recorded after approval.</div>}<div className="mt-5 rounded-xl border border-coral-100 bg-coral-50/50 p-4 text-sm leading-6 text-slate-700">{selected.status === "blocked" ? "The gateway blocked this action. It is not forwarded." : "Approving forwards the saved arguments to the tool server once. Rejecting leaves the call unforwarded."}</div>{canDecide && <div className="mt-5 flex gap-3"><button type="button" onClick={() => void resolve(selected.action_id, "approved")} className="h-10 rounded-xl bg-emerald-600 px-3.5 text-sm font-semibold text-white">Approve</button><button type="button" onClick={() => void resolve(selected.action_id, "rejected")} className="h-10 rounded-xl px-3.5 text-sm font-semibold text-rose-700 hover:bg-rose-50">Reject</button></div>}</section></div>;
    })()}
  </>;
}
