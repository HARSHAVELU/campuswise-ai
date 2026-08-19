// Browser-safe API helper for client components. Unlike lib/api.ts (server-only,
// which can use the Docker-internal API_BASE_URL), this always uses the
// browser-visible NEXT_PUBLIC_API_BASE_URL since it runs on the client.
const BROWSER_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiClientError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BROWSER_API_BASE_URL}/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiClientError(res.status, `Request to ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}
