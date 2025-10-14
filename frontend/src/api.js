const base = '' // la SPA se sirve desde el mismo dominio que el backend

export async function api(path, { method = 'GET', body, token } = {}) {
    const res = await fetch(base + path, {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: body ? JSON.stringify(body) : undefined
    })
    if (!res.ok) throw new Error((await res.json()).detail || 'Error de red')
    return res.json()
}
