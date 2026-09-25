"use client";

import { useEffect, useRef, useState } from "react";
import type { Policy } from "@/lib/types";
import { categoryLabel, enforcementTypeLabel, PolicyStatusBadge } from "./policy-badges";

const statusChoices = [
  { status: "active", label: "Active" },
  { status: "inactive", label: "Inactive" },
  { status: "draft", label: "Park" },
] as const satisfies ReadonlyArray<{ status: Policy["status"]; label: string }>;

function StatusMenu({ status, onSelect }: { status: Policy["status"]; onSelect: (status: Policy["status"]) => void }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    function close(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);
  if (status === "pending_review") return <PolicyStatusBadge status={status} />;
  return <div ref={menuRef} className="relative"><button type="button" aria-expanded={open} aria-haspopup="listbox" onClick={() => setOpen((current) => !current)} className="rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-coral-500"><PolicyStatusBadge status={status} /></button>{open && <ul role="listbox" className="absolute left-0 z-20 mt-2 w-36 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg">{statusChoices.map((choice) => <li key={choice.status}><button type="button" role="option" aria-selected={choice.status === status} onClick={() => { setOpen(false); if (choice.status !== status) onSelect(choice.status); }} className={`flex w-full px-3 py-2 text-left text-sm ${choice.status === status ? "font-semibold text-slate-950" : "text-slate-700 hover:bg-slate-50"}`}>{choice.label}</button></li>)}</ul>}</div>;
}

function formatAction(action: string) {
  return action.split("_").join(" ");
}

export function PolicyTable({ policies, onStatusChange }: { policies: Policy[]; onStatusChange: (policyId: string, status: Policy["status"]) => Promise<void> }) {
  if (policies.length === 0) {
    return <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center shadow-sm"><span className="mx-auto flex size-10 items-center justify-center rounded-xl bg-coral-50 text-coral-700">+</span><h3 className="mt-4 text-base font-semibold text-slate-900">No policies yet</h3><p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">Upload a company policy document to begin extracting structured rules for review.</p></div>;
  }

  return <>
    <div className="hidden overflow-visible rounded-2xl border border-slate-200/90 bg-white shadow-[0_1px_2px_rgba(15,23,42,0.03),0_10px_28px_rgba(15,23,42,0.025)] lg:block"><table className="w-full text-left"><thead className="border-b border-slate-200/80 bg-slate-50/80 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500"><tr><th className="px-5 py-3.5">Policy</th><th className="px-4 py-3.5">Category</th><th className="px-4 py-3.5">Enforcement type</th><th className="px-4 py-3.5">Status</th><th className="px-4 py-3.5">Scope</th><th className="px-5 py-3.5">Source</th></tr></thead><tbody className="divide-y divide-slate-100/90">{policies.map((policy) => <tr key={policy.policy_id} className="align-top transition-colors duration-150 hover:bg-coral-50/[0.35]"><td className="px-5 py-4.5"><p className="font-semibold tracking-[-0.015em] text-slate-900">{policy.name}</p><p className="mt-1 font-mono text-xs text-slate-500">{formatAction(policy.action)}{policy.priority == null ? "" : ` · priority ${policy.priority}`}</p></td><td className="px-4 py-4.5"><p className="text-sm text-slate-700">{categoryLabel(policy.category)}</p></td><td className="px-4 py-4.5"><p className="text-sm text-slate-800">{enforcementTypeLabel(policy.decision)}</p>{policy.approval_role && <p className="mt-1.5 text-xs capitalize text-slate-500">{policy.approval_role.replace("_", " ")}</p>}</td><td className="px-4 py-4.5"><StatusMenu status={policy.status} onSelect={(status) => void onStatusChange(policy.policy_id, status)} /></td><td className="px-4 py-4.5"><p className="text-sm text-slate-700">{policy.subject?.roles?.join(", ") || "Any role"}</p><p className="mt-1 text-xs text-slate-500">{policy.conditions.length === 0 ? "Always applies" : `${policy.conditions.length} condition${policy.conditions.length === 1 ? "" : "s"}`}</p></td><td className="px-5 py-4.5"><p className="font-mono text-xs text-slate-600">{policy.source_doc ?? "No source document"}</p></td></tr>)}</tbody></table></div>
    <div className="space-y-4 lg:hidden">{policies.map((policy) => <article key={policy.policy_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-slate-900">{policy.name}</h3><p className="mt-1 font-mono text-xs text-slate-500">{formatAction(policy.action)}</p></div><StatusMenu status={policy.status} onSelect={(status) => void onStatusChange(policy.policy_id, status)} /></div><p className="mt-4 text-sm text-slate-600">{categoryLabel(policy.category)} · {enforcementTypeLabel(policy.decision)}</p><dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-slate-100 pt-4 text-sm"><div><dt className="text-slate-500">Bound roles</dt><dd className="mt-1 text-slate-700">{policy.subject?.roles?.join(", ") || "Any role"}</dd></div><div><dt className="text-slate-500">Conditions</dt><dd className="mt-1 text-slate-700">{policy.conditions.length === 0 ? "Always applies" : `${policy.conditions.length} condition${policy.conditions.length === 1 ? "" : "s"}`}</dd></div><div><dt className="text-slate-500">Priority</dt><dd className="mt-1 text-slate-700">{policy.priority ?? "—"}</dd></div><div><dt className="text-slate-500">Source</dt><dd className="mt-1 font-mono text-xs text-slate-700">{policy.source_doc ?? "Not available"}</dd></div></dl></article>)}</div>
  </>;
}
