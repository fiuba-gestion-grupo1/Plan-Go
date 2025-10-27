import React, { useEffect, useState } from "react";

export default function Suggestions({ token, me }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        setErr("");
        const res = await fetch("/api/suggestions", {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) {
          const j = await res.json().catch(() => ({}));
          throw new Error(j.detail || `HTTP ${res.status}`);
        }
        const data = await res.json();
        if (!cancel) setItems(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancel) setErr(e.message || "Error al cargar sugerencias");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [token]);

  return (
    <div className="container py-3">
      <h2 className="mb-3">Sugerencias para {me?.first_name || me?.username}</h2>

      {loading && <div className="alert alert-info">Cargando…</div>}
      {err && <div className="alert alert-danger">{err}</div>}

      {!loading && items.length === 0 && !err && (
        <div className="alert alert-secondary">
          No hay sugerencias aún. Completá tus preferencias para ver resultados.
        </div>
      )}

      <div className="row">
        {items.map((it) => (
          <div key={it.id} className="col-md-4 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <h5 className="card-title">{it.title || it.place_name || `Pub #${it.id}`}</h5>
                <p className="card-text">
                  Puntaje: <strong>{it.score}</strong>
                </p>
                <a
                className="btn btn-sm btn-outline-primary"
                href={`/?pub=${it.id}`}
                title="Ver reseñas"
                >
                Ver reseñas
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
