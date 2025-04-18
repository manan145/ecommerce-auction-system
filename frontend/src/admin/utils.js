// helper for authenticated requests
export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("token");
  const opts = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  };
  const res = await fetch(url, opts);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}
