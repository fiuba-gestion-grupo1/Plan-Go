import React, { useEffect, useState } from "react"; // Importamos React y hooks
import { request } from "../utils/api"; // Importamos el helper de requests
import PublicationDetailModal from "../components/PublicationDetailModal"; // Componente del modal de detalles
import { RatingBadge, Stars } from "../components/shared/UIComponents"; // Componente de badge de rating


/* --- COMPONENTE PRINCIPAL DE SUGERENCIAS --- */
export default function Suggestions({ token, me }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [sortOrder, setSortOrder] = useState("desc");

  const [openDetailModal, setOpenDetailModal] = useState(false);
  const [currentPub, setCurrentPub] = useState(null);

  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

  /* ... (la función toggleFavorite no cambia) ... */
  async function toggleFavorite(pubId) {
    try {
      const data = await request(`/api/publications/${pubId}/favorite`, {
        method: "POST",
        token
      });
      setItems(prevPubs =>
        prevPubs.map(p =>
          p.id === pubId ? { ...p, is_favorite: data.is_favorite } : p
        )
      );
      if (currentPub && currentPub.id === pubId) {
        setCurrentPub(p => ({ ...p, is_favorite: data.is_favorite }));
      }
    } catch (e) {
      setErr(e.message);
    }
  }

  // --- Carga de datos (Original de Suggestions) ---
  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(`/api/suggestions?sort=${sortOrder}`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store" // <-- Añadido para evitar caché del navegador
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
  }, [token, sortOrder]);

  return (
    <div className="container py-3">

      {/* --- INICIO DE LA CORRECCIÓN DE ALINEACIÓN --- */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        {/* Título */}
        <h2 className="mb-0">💡 Sugerencias para {me?.first_name || me?.username}</h2>

        {/* Filtro (solo se muestra si hay items) */}
        {!loading && items.length > 0 && !err && (
          <div style={{ maxWidth: '250px' }}>
            <label htmlFor="sort-select" className="form-label small text-muted mb-1">Ordenar por</label>
            <select
              id="sort-select"
              className="form-select form-select-sm"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)} // Actualiza el estado
            >
              <option value="desc">Mayor Coincidencia</option>
              <option value="asc">Menor Coincidencia</option>
            </select>
          </div>
        )}
      </div>
      {/* --- FIN DE LA CORRECCIÓN DE ALINEACIÓN --- */}


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

      {/* El div del filtro ya no está aquí */}
      {!loading && items.length > 0 && !err && (
        <>
          {/* --- GRILLA DE PUBLICACIONES (el div.row original) --- */}
          <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
            {items.map((pub) => (
              <div className="col" key={pub.id}>
                {/* ... (El código de la tarjeta no cambia) ... */}
                <div
                  className="card shadow-sm h-100"
                  onClick={() => openPublicationDetail(pub)}
                  style={{ cursor: "pointer" }}
                >
                  <div className="card-body pb-0">
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="flex-grow-1">
                        <h5 className="card-title mb-1">{pub.place_name}</h5>
                        <small className="text-muted">📍 {pub.address ? `${pub.address}, ` : ""}{pub.city}, {pub.province}{pub.country ? `, ${pub.country}` : ""}</small>
                        <div className="mt-2 d-flex flex-wrap gap-2">
                          <RatingBadge avg={pub.rating_avg} count={pub.rating_count} />
                          {(pub.categories || []).map((c) => (
                            <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                          ))}
                        </div>
                        <p className="card-text mt-2 mb-0">
                          <span className="text-success fw-bold">${pub.cost_per_day}</span>
                        </p>
                      </div>
                      <button
                        className="btn btn-link p-0 ms-2"
                        onClick={(e) => { e.stopPropagation(); toggleFavorite(pub.id); }}
                        style={{ fontSize: "1.5rem", textDecoration: "none" }}
                        title={pub.is_favorite ? "Quitar de favoritos" : "Agregar a favoritos"}
                      >
                        {pub.is_favorite ? "❤️" : "🤍"}
                      </button>
                    </div>
                  </div>
                  {pub.photos?.length ? (
                    <div id={`home-carousel-${pub.id}`} className="carousel slide" data-bs-ride="false">
                      <div className="carousel-inner">
                        {pub.photos.map((url, idx) => (
                          <div className={`carousel-item ${idx === 0 ? "active" : ""}`} key={url}>
                            <img
                              src={url}
                              className="d-block w-100"
                              alt={`Foto ${idx + 1}`}
                              style={{ height: 260, objectFit: "cover" }}
                            />
                          </div>
                        ))}
                      </div>
                      {pub.photos.length > 1 && (
                        <>
                          <button className="carousel-control-prev" type="button" data-bs-target={`#home-carousel-${pub.id}`} data-bs-slide="prev">
                            <span className="carousel-control-prev-icon" aria-hidden="true" />
                          </button>
                          <button className="carousel-control-next" type="button" data-bs-target={`#home-carousel-${pub.id}`} data-bs-slide="next">
                            <span className="carousel-control-next-icon" aria-hidden="true" />
                          </button>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-muted">Sin fotos</div>
                  )}
                  <div className="card-footer bg-white d-flex justify-content-between align-items-center">
                    <small className="text-muted">Creado: {new Date(pub.created_at).toLocaleString()}</small>
                    <button
                      className="btn btn-sm btn-celeste"
                      onClick={(e) => { e.stopPropagation(); openPublicationDetail(pub); }}
                    >
                      Ver Detalles
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* --- El modal de detalles no cambia --- */}
      <PublicationDetailModal
        open={openDetailModal}
        pub={currentPub}
        token={token}
        me={me}
        onClose={() => setOpenDetailModal(false)}
        onToggleFavorite={toggleFavorite}
      />
    </div>
  );
}