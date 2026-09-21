// Thin API client for the (future) backend gateway.
// Point NEXT_PUBLIC_API_URL at the backend once it exists; until then, pages can use mock-data.ts.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Placeholder — flesh out endpoints (upload, policies, actions, approvals) when the backend lands.
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  return res.json() as Promise<T>;
}
