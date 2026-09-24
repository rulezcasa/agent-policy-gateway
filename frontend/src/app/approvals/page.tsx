"use client";

import { useCallback, useEffect, useState } from "react";

import { API_URL } from "@/lib/api";

type PendingTask = {
  action_id: string;
  status: string;
  tool: string;
  arguments: Record<string, unknown>;
  normalized_arguments?: Record<string, unknown>;
  decision: string;
  policy_ids?: string[];
  required_approval?: string | null;
  llm_reasoning?: string | null;
  agent_id?: string;
};

export default function ApprovalsPage() {
  const [tasks, setTasks] = useState<PendingTask[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/approvals`);
      if (!res.ok) throw new Error(`Could not load approvals (${res.status})`);
      setTasks(await res.json());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load approvals");
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), 2000);
    return () => clearInterval(timer);
  }, [load]);

  async function decide(actionId: string, outcome: "approved" | "rejected") {
    const res = await fetch(`${API_URL}/api/approvals/${actionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ outcome, by: "manager_priya" }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(body.detail ?? `Could not ${outcome} ${actionId}`);
    }
    await load();
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-4 p-8">
      <h1 className="text-2xl font-semibold">Approvals</h1>
      <p className="text-sm text-zinc-600">
        Held tool calls show up here. Approving one runs it and sends the result back to the open chat.
      </p>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {tasks.length === 0 ? <p className="text-sm text-zinc-500">No held requests yet.</p> : null}
      {tasks.map((task) => (
        <article key={task.action_id} className="rounded-lg border border-zinc-200 p-4">
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="font-medium">{task.tool}</h2>
            <span className="text-xs uppercase tracking-wide text-zinc-500">{task.status}</span>
          </div>
          <p className="mt-2 text-sm">{task.llm_reasoning}</p>
          <dl className="mt-3 grid grid-cols-[8rem_1fr] gap-y-1 text-sm">
            <dt className="text-zinc-500">Decision</dt>
            <dd>{task.decision}</dd>
            <dt className="text-zinc-500">Needs</dt>
            <dd>{task.required_approval ?? "—"}</dd>
            <dt className="text-zinc-500">Agent</dt>
            <dd>{task.agent_id}</dd>
            <dt className="text-zinc-500">Arguments</dt>
            <dd className="font-mono text-xs">{JSON.stringify(task.normalized_arguments ?? task.arguments)}</dd>
          </dl>
          {task.status === "pending_approval" ? (
            <div className="mt-4 flex gap-2">
              <button
                className="rounded bg-black px-3 py-1.5 text-sm text-white"
                onClick={() => void decide(task.action_id, "approved")}
                type="button"
              >
                Approve
              </button>
              <button
                className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
                onClick={() => void decide(task.action_id, "rejected")}
                type="button"
              >
                Reject
              </button>
            </div>
          ) : null}
        </article>
      ))}
    </main>
  );
}
