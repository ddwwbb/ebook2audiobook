const API_BASE = "/api";

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => fetchJSON<T>(path),
  post: <T>(path: string, body?: unknown) =>
    fetchJSON<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    fetchJSON<T>(path, { method: "PUT", body: JSON.stringify(body) }),
};

export { API_BASE };
