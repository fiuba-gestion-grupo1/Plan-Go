const base = '' // la SPA se sirve desde el mismo dominio que el backend

export async function api(path, { method = 'GET', body, token } = {}) {
  const res = await fetch(path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });

  const raw = await res.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch { data = { detail: raw }; }

  if (!res.ok) throw new Error(data.detail || 'Error de red');
  return data;
}

