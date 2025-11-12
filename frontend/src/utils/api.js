/**
 * Utilidad para hacer peticiones HTTP a la API
 */
export async function request(path, { method = "GET", token, body, isForm = false } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isForm) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { method, headers, body: isForm ? body : body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    console.error("Error del servidor:", err);
    // Si es un error de validación de FastAPI
    if (err.detail && Array.isArray(err.detail)) {
      const messages = err.detail.map(e => `${e.loc?.join('.')} - ${e.msg}`).join(', ');
      throw new Error(messages);
    }
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }
  return res.json().catch(() => ({}));
}


/**
 * Hook personalizado para obtener el token del localStorage
 */
export function useToken() {
  return localStorage.getItem("token") || "";
}