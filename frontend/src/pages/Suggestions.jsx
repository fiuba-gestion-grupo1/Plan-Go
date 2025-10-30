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
      <h2 className="mb-4">💡 Sugerencias para {me?.first_name || me?.username}</h2>
      
      <div className="alert alert-info mb-4">
        <strong>Tip:</strong> Estas sugerencias se basan en tus preferencias de viaje. 
        Asegúrate de tener tus preferencias actualizadas para obtener mejores recomendaciones.
      </div>

      {loading && <div className="alert alert-info">Cargando sugerencias…</div>}
      {err && <div className="alert alert-danger">{err}</div>}

      {!loading && items.length === 0 && !err && (
        <div className="alert alert-secondary">
          No hay sugerencias aún. Completá tus preferencias para ver resultados personalizados.
        </div>
      )}

      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
        {items.map((it) => (
          <div key={it.id} className="col">
            <div className="card h-100 shadow-sm">
              <div className="card-body">
                <h5 className="card-title">{it.title || it.place_name || `Publicación #${it.id}`}</h5>
                {it.city && it.country && (
                  <p className="text-muted small mb-3">
                    📍 {it.city}, {it.country}
                  </p>
                )}
                <p className="card-text text-muted small">
                  Esta publicación coincide con tus preferencias de viaje.
                </p>
              </div>
              <div className="card-footer bg-white">
                <small className="text-muted">Sugerencia personalizada</small>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
