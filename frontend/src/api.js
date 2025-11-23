export const BASE_URL = 'http://localhost:8000';

export async function api(path, { method = 'GET', body, token, useAuth = true } = {}) {
  const storedToken =
    typeof window !== 'undefined'
      ? (localStorage.getItem('access_token') || localStorage.getItem('token'))
      : null;

  const finalToken = token ?? (useAuth ? storedToken : null);

  const headers = {
    ...(finalToken ? { Authorization: `Bearer ${finalToken}` } : {})
  };

  let finalBody = body;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    finalBody = JSON.stringify(body);
  }

  const fullUrl = path.startsWith('http') ? path : `${BASE_URL}${path}`;

  const res = await fetch(fullUrl, {
    method,
    headers,
    body: finalBody
  });

  const raw = await res.text();
  let data;
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { detail: raw };
  }

  if (!res.ok) {
    const error = new Error(data.detail || 'Ocurrió un error');
    error.status = res.status;
    error.detail = data.detail;
    throw error;
  }

  return data;
}
