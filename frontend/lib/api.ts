export async function api<T>(path: string, options: RequestInit = {}) {
  const res = await fetch(`/api${path}`, {
    ...options,
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data?.message || data?.detail || data?.error
    throw new Error(detail ? `${detail} (HTTP ${res.status})` : `Request failed (HTTP ${res.status})`)
  }
  return data as T
}
