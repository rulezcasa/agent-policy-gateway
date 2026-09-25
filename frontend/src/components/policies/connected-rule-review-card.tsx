"use client";

import { useState } from "react";
import type { Decision, GatewayTool, IngestionPolicy, IngestionPolicyUpdate, PolicyCondition } from "@/lib/types";
import { enforcementTypeLabel, PolicyStatusBadge } from "./policy-badges";

function conditionText(conditions: PolicyCondition[]) {
  return conditions.length === 0 ? "Always applies" : conditions.map((condition) => `${condition.field} ${condition.operator} ${Array.isArray(condition.value) ? condition.value.join(", ") : condition.value}${condition.unit ? ` ${condition.unit}` : ""}`).join(" · ");
}

function toolFields(tool: GatewayTool) {
  return Object.keys(tool.parameters.properties ?? {});
}

export function ConnectedRuleReviewCard({ policy, tools, onConfirm, onPark, onDeactivate, onEdit }: { policy: IngestionPolicy; tools: GatewayTool[]; onConfirm: () => Promise<void>; onPark: () => Promise<void>; onDeactivate: () => Promise<void>; onEdit: (update: IngestionPolicyUpdate) => Promise<void> }) {
  const [editing, setEditing] = useState(false);
  const [mapping, setMapping] = useState(false);
  const [draft, setDraft] = useState(policy);
  const [conditionsInput, setConditionsInput] = useState(() => JSON.stringify(policy.conditions, null, 2));
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runMutation(mutation: () => Promise<void>) {
    setIsSaving(true); setError(null);
    try { await mutation(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save this rule."); } finally { setIsSaving(false); }
  }

  function saveEdit() {
    let conditions: PolicyCondition[];
    try {
      const parsed = JSON.parse(conditionsInput) as unknown;
      if (!Array.isArray(parsed)) throw new Error();
      conditions = parsed as PolicyCondition[];
    } catch { setError("Conditions must be a valid JSON array."); return; }
    const update: IngestionPolicyUpdate = {};
    if (draft.name !== policy.name) update.name = draft.name;
    if (draft.category !== policy.category) update.category = draft.category;
    if (draft.action !== policy.action) update.action = draft.action;
    if (draft.decision !== policy.decision) update.decision = draft.decision;
    if (draft.approval_role !== policy.approval_role) update.approval_role = draft.approval_role;
    if (JSON.stringify(conditions) !== JSON.stringify(policy.conditions)) update.conditions = conditions;
    if (Object.keys(update).length === 0) { setEditing(false); return; }
    void runMutation(async () => { await onEdit(update); setEditing(false); });
  }

  const actionIsMapped = tools.some((tool) => tool.name === policy.action);
  const canConfirm = policy.status === "pending_review" || policy.status === "draft";

  return <article className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.03),0_10px_28px_rgba(15,23,42,0.025)]"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex flex-wrap items-center gap-2"><PolicyStatusBadge status={policy.status} /></div><h3 className="mt-3 text-lg font-semibold tracking-[-0.02em] text-slate-950">{policy.name}</h3><p className="mt-1 font-mono text-xs text-slate-500">{policy.policy_id} · {policy.source_doc ?? "Source unavailable"}</p></div><p className="text-sm text-slate-700">{enforcementTypeLabel(policy.decision)}</p></div>
    {policy.needs_review && !actionIsMapped && <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><p><span className="font-semibold">Needs closer review.</span> The extracted action did not match a known tool.</p><button type="button" disabled={isSaving} onClick={() => setMapping((open) => !open)} className="h-9 shrink-0 rounded-lg bg-amber-800 px-3 text-sm font-semibold text-white hover:bg-amber-900 disabled:cursor-not-allowed disabled:opacity-60">{mapping ? "Hide tools" : "Map to a tool"}</button></div>
      {mapping && <div className="mt-4 space-y-2">{tools.length === 0 ? <p>No tools are available from the gateway right now.</p> : tools.map((tool) => { const fields = toolFields(tool); return <button key={tool.name} type="button" disabled={isSaving} onClick={() => void runMutation(async () => { await onEdit({ action: tool.name }); setMapping(false); })} className="flex w-full flex-col items-start rounded-lg border border-amber-200 bg-white px-3 py-2.5 text-left hover:border-amber-400 disabled:cursor-not-allowed disabled:opacity-60"><span className="font-mono text-sm font-semibold text-slate-900">{tool.name}</span><span className="mt-1 text-sm text-slate-600">{tool.description}</span>{fields.length > 0 && <span className="mt-1 font-mono text-xs text-slate-500">{fields.join(", ")}</span>}</button>; })}</div>}
    </div>}
    <div className="mt-6 grid gap-4 lg:grid-cols-2"><section className="rounded-xl border border-slate-100 bg-slate-50/80 p-5"><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">Original policy text</p><blockquote className="mt-3 border-l-2 border-coral-200 pl-3 text-sm leading-6 text-slate-700">“{policy.original_text ?? "No original source text is available."}”</blockquote></section><section className="rounded-xl border border-slate-200 bg-white p-5"><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">Structured rule</p><dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm"><div><dt className="text-slate-500">Action</dt><dd className="mt-1 font-mono text-slate-800">{policy.action}</dd></div><div><dt className="text-slate-500">Scope</dt><dd className="mt-1 text-slate-800">{policy.subject.roles.join(", ")}</dd></div><div className="col-span-2"><dt className="text-slate-500">Conditions</dt><dd className="mt-1 text-slate-800">{conditionText(policy.conditions)}</dd></div>{policy.approval_role && <div><dt className="text-slate-500">Required approval</dt><dd className="mt-1 capitalize text-slate-800">{policy.approval_role.replaceAll("_", " ")}</dd></div>}</dl></section></div>
    {error && <p role="alert" className="mt-4 text-sm text-rose-700">{error}</p>}
    {canConfirm ? <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4"><button type="button" disabled={isSaving} onClick={() => void runMutation(onConfirm)} className="h-10 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm shadow-emerald-100 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60">{isSaving ? "Saving..." : "Confirm rule"}</button><button type="button" disabled={isSaving} onClick={() => { setDraft(policy); setConditionsInput(JSON.stringify(policy.conditions, null, 2)); setEditing(true); }} className="h-10 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60">Edit</button>{policy.status !== "draft" && <button type="button" disabled={isSaving} onClick={() => void runMutation(onPark)} className="h-10 rounded-xl px-4 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60">Park rule</button>}</div> : <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4"><p className="text-sm text-slate-500">{policy.status === "active" ? "This rule is active and enforced by the gateway." : "This rule is inactive and is not enforced."}</p>{policy.status === "active" && <button type="button" disabled={isSaving} onClick={() => void runMutation(onDeactivate)} className="h-10 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60">{isSaving ? "Saving..." : "Make inactive"}</button>}</div>}
    {editing && <div className="mt-5 rounded-xl border border-coral-200 bg-coral-50/50 p-4"><h4 className="font-semibold text-slate-900">Edit structured rule</h4><p className="mt-1 text-sm text-slate-600">Changes are saved to the review queue and remain pending until you confirm the rule.</p><div className="mt-4 grid gap-3 sm:grid-cols-2"><label className="text-sm font-medium text-slate-700">Rule name<input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-coral-500" /></label><label className="text-sm font-medium text-slate-700">Category<input value={draft.category} onChange={(event) => setDraft({ ...draft, category: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-coral-500" /></label><label className="text-sm font-medium text-slate-700">Action<input value={draft.action} onChange={(event) => setDraft({ ...draft, action: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-coral-500" /></label><label className="text-sm font-medium text-slate-700">Decision<select value={draft.decision} onChange={(event) => setDraft({ ...draft, decision: event.target.value as Decision })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-coral-500"><option value="allow">Allow</option><option value="block">Block</option><option value="requires_approval">Requires approval</option></select></label><label className="text-sm font-medium text-slate-700 sm:col-span-2">Approval role<input value={draft.approval_role ?? ""} onChange={(event) => setDraft({ ...draft, approval_role: event.target.value || undefined })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-coral-500" /></label><label className="text-sm font-medium text-slate-700 sm:col-span-2">Conditions (JSON array)<textarea value={conditionsInput} onChange={(event) => setConditionsInput(event.target.value)} rows={5} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-xs text-slate-900 outline-none focus:border-coral-500" /></label></div><div className="mt-4 flex gap-3"><button type="button" disabled={isSaving} onClick={saveEdit} className="rounded-lg bg-coral-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-coral-700 disabled:cursor-not-allowed disabled:opacity-60">Save changes</button><button type="button" disabled={isSaving} onClick={() => { setDraft(policy); setConditionsInput(JSON.stringify(policy.conditions, null, 2)); setEditing(false); setError(null); }} className="rounded-lg px-3.5 py-2 text-sm font-semibold text-slate-600 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60">Cancel</button></div></div>}
  </article>;
}
