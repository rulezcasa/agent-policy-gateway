// Thin API client for the gateway backend. NEXT_PUBLIC_API_URL can override
// the local development default when the frontend is deployed elsewhere.

import type { IngestionPolicy, IngestionPolicyUpdate } from "./types";

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
        const parsed = JSON.parse(body) as { detail?: string; message?: string };
        message = parsed.detail ?? parsed.message ?? message;
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

export function updateIngestionPolicy(policyId: string, update: IngestionPolicyUpdate): Promise<IngestionPolicy> {
  return apiFetch<IngestionPolicy>(`/api/ingestion/policies/${encodeURIComponent(policyId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
}
