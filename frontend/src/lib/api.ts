// Thin API client for the gateway backend. NEXT_PUBLIC_API_URL can override
// the local development default when the frontend is deployed elsewhere.

import type { GatewayTool, IngestionPolicy, IngestionPolicyUpdate, PendingTask, RecordedAction } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    let message = `Request failed (${res.status}).`;
    if (body) {
      try {
        const parsed = JSON.parse(body) as { detail?: unknown; message?: string };
        if (typeof parsed.detail === "string") message = parsed.detail;
        else if (Array.isArray(parsed.detail)) {
          message = parsed.detail.map((item) => (item && typeof item === "object" && "msg" in item ? String(item.msg) : JSON.stringify(item))).join(" ");
        } else if (parsed.message) message = parsed.message;
      } catch {
        message = body;
      }
    }
    throw new ApiError(message, res.status);
  }
  return res.json() as Promise<T>;
}

export function uploadPolicies(files: File[]): Promise<IngestionPolicy[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  return apiFetch<IngestionPolicy[]>("/api/policies/upload", { method: "POST", body: formData });
}

export function getIngestionPolicies(): Promise<IngestionPolicy[]> {
  return apiFetch<IngestionPolicy[]>("/api/ingestion/policies", { cache: "no-store" });
}

export function getIngestionTools(): Promise<GatewayTool[]> {
  return apiFetch<GatewayTool[]>("/api/ingestion/tools", { cache: "no-store" });
}

export function getActions(): Promise<RecordedAction[]> {
  return apiFetch<RecordedAction[]>("/api/actions", { cache: "no-store" });
}

export function getApprovals(): Promise<PendingTask[]> {
  return apiFetch<PendingTask[]>("/api/approvals", { cache: "no-store" });
}

export function decideApproval(actionId: string, outcome: "approved" | "rejected", by = "manager"): Promise<PendingTask> {
  return apiFetch<PendingTask>(`/api/approvals/${encodeURIComponent(actionId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outcome, by }),
  });
}

export function updateIngestionPolicy(policyId: string, update: IngestionPolicyUpdate): Promise<IngestionPolicy> {
  return apiFetch<IngestionPolicy>(`/api/ingestion/policies/${encodeURIComponent(policyId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
}
