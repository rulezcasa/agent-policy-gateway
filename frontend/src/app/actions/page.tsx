"use client";

import { useEffect, useState } from "react";

import { API_URL } from "@/lib/api";

type ActionRecord = {
  action_id: string;
  tool: string;
  decision: string;
  normalized_arguments?: Record<string, unknown>;
  llm_reasoning?: string | null;
  required_approval?: string | null;
  timestamp?: string;
};

export default function ActionsPage() {
  const [actions, setActions] = useState<ActionRecord[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const res = await fetch(`${API_URL}/api/actions`);
      if (!res.ok || cancelled) return;
      setActions(await res.json());
    }
    void load();
    const timer = setInterval(() => void load(), 2000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-4 p-8">
      <h1 className="text-2xl font-semibold">Actions</h1>
      {actions.length === 0 ? <p className="text-sm text-zinc-500">No intercepted calls yet.</p> : null}
      {actions.map((action) => (
        <article key={action.action_id} className="rounded-lg border border-zinc-200 p-4 text-sm">
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="font-medium">{action.tool}</h2>
            <span className="text-xs uppercase tracking-wide text-zinc-500">{action.decision}</span>
          </div>
          {action.llm_reasoning ? <p className="mt-2">{action.llm_reasoning}</p> : null}
          <p className="mt-2 font-mono text-xs text-zinc-600">
            {JSON.stringify(action.normalized_arguments ?? {})}
          </p>
          {action.required_approval ? (
            <p className="mt-2 text-zinc-600">Approval: {action.required_approval}</p>
          ) : null}
        </article>
      ))}
    </main>
  );
}
