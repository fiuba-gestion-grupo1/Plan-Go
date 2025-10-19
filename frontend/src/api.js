export const BASE_URL = ''; // la SPA se sirve desde el mismo dominio que el backend

export async function api(path, { method = 'GET', body, token } = {}) {
  
  const headers = {
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };

  let finalBody = body;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    finalBody = JSON.stringify(body);
  }

  const res = await fetch(path, {
    method,
    headers,
    body: finalBody
  });

  const raw = await res.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch { data = { detail: raw }; }

  if (!res.ok) {
    const error = new Error(data.detail || 'Ocurrió un error');
    error.status = res.status;
    error.detail = data.detail; 
    throw error;
  }
  
  return data;
}