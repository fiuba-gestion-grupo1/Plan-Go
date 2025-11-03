import React, { useEffect, useState } from "react"; // Importamos React y hooks

/* ... (Las funciones request, Stars, y RatingBadge no cambian) ... */
async function request(path, { method = "GET", token, body, isForm = false } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isForm) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { method, headers, body: isForm ? body : body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    console.error("Error del servidor:", err);
    if (err.detail && Array.isArray(err.detail)) {
      const messages = err.detail.map(e => `${e.loc?.join('.')} - ${e.msg}`).join(', ');
      throw new Error(messages);
    }
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }
  return res.json().catch(() => ({}));
}

function Stars({ value = 0 }) {
  const pct = Math.max(0, Math.min(100, (Number(value) / 5) * 100));
  return (
    <span className="position-relative" aria-label={`Rating ${value}/5`}>
      <span className="text-muted" style={{ letterSpacing: 1 }}>★★★★★</span>
      <span className="position-absolute top-0 start-0 overflow-hidden" style={{ width: `${pct}%` }}>
        <span className="text-warning" style={{ letterSpacing: 1 }}>★★★★★</span>
      </span>
    </span>
  );
}
function RatingBadge({ avg = 0, count = 0 }) {
  return (
    <span className="badge bg-light text-dark border">
      <Stars value={avg} /> <span className="ms-1">{Number(avg).toFixed(1)} • {count} reseña{count === 1 ? "" : "s"}</span>
    </span>
  );
}


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

function PublicationDetailModal({ open, pub, onClose, onToggleFavorite, me, token }) {
  if (!open || !pub) return null;

  const [isFav, setIsFav] = useState(pub.is_favorite || false);
  useEffect(() => { setIsFav(pub.is_favorite || false); }, [pub?.id, pub?.is_favorite]);

  // --- logica de reseñas---
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const isPremium = me?.role === "premium" || me?.username === "admin";

  // Efecto para cargar reseñas cuando se abre el modal o cambia la publicación
  useEffect(() => {
    if (!open || !pub?.id) {
      setList([]); // Limpiar lista si se cierra
      setErr("");
      return;
    }
    let cancel = false;
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const rows = await request(`/api/publications/${pub.id}/reviews`);
        if (!cancel) setList(rows);
      } catch (e) {
        if (!cancel) setErr(e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [open, pub?.id]); // Depende de 'open' y 'pub.id'

  // Función para enviar reseña
  async function submitReview(e) {
    e.preventDefault();
    if (!isPremium) { return; }
    if (!token) { alert("Iniciá sesión para publicar una reseña."); return; }
    try {
      await request(`/api/publications/${pub.id}/reviews`, {
        method: "POST",
        token,
        body: { rating: Number(rating), comment: comment || undefined }
      });
      setComment(""); setRating(5);
      // Recargar la lista de reseñas
      const rows = await request(`/api/publications/${pub.id}/reviews`);
      setList(rows);
      // Nota: El rating_avg/count de 'pub' (prop) no se actualizará
      // hasta que se cierre y reabra el modal.
    } catch (e) {
      alert(`Error creando reseña: ${e.message}`);
    }
  }

  async function handleToggleFavorite(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    const prev = isFav;
    setIsFav(!prev); // update optimista
    try {
      if (onToggleFavorite) await onToggleFavorite(pub.id);
    } catch (err) {
      setIsFav(prev); // rollback
      alert('Error actualizando favoritos: ' + (err?.message || err));
    }
  }

  return (
    <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
      style={{ background: "rgba(0,0,0,.4)", zIndex: 1050 }}>
      <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 600, maxHeight: "90vh", width: "90%" }}>

        {/* Header con botón cerrar */}
        <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
          <h5 className="mb-0">{pub.place_name}</h5>
          <button className="btn-close" onClick={onClose}></button>
        </div>

        {/* Contenido scrolleable */}
        <div className="p-3" style={{ overflowY: "auto", maxHeight: "calc(90vh - 70px)" }}>

          {/* Carrusel de imágenes */}
          <div className="mb-3">
            {pub.photos?.length > 0 ? ( // <--- CAMBIADO
              <div id={`carousel-${pub.id}`} className="carousel slide" data-bs-ride="carousel">
                <div className="carousel-inner">
                  {pub.photos.map((img, i) => ( // <--- CAMBIADO
                    <div key={i} className={`carousel-item ${i === 0 ? 'active' : ''}`}>
                      <img src={img} className="d-block w-100 rounded" alt={`Imagen ${i + 1}`}
                        style={{ height: "300px", objectFit: "cover" }} />
                    </div>
                  ))}
                </div>
                {pub.photos.length > 1 && ( // <--- CAMBIADO
                  <>
                    <button className="carousel-control-prev" type="button"
                      data-bs-target={`#carousel-${pub.id}`} data-bs-slide="prev">
                      <span className="carousel-control-prev-icon"></span>
                    </button>
                    <button className="carousel-control-next" type="button"
                      data-bs-target={`#carousel-${pub.id}`} data-bs-slide="next">
                      <span className="carousel-control-next-icon"></span>
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="text-muted text-center p-4">Sin imágenes disponibles</div>
            )}
          </div>

          {/* Información principal */}
          <div className="mb-3">

            {/* Renglón 1: Reseñas y Favorito */}
            <div className="d-flex justify-content-between align-items-start mb-2">
              <div>
                <RatingBadge avg={pub.rating_avg} count={pub.rating_count} />
              </div>
              <button
                className={`btn ${isFav ? 'btn-danger' : 'btn-outline-danger'}`}
                onClick={handleToggleFavorite}
                title={isFav ? 'Quitar de favoritos' : 'Agregar a favoritos'}
              >
                {isFav ? '❤️ Favorito' : '🤍 Agregar a favoritos'}
              </button>
            </div>

            {/* --- BLOQUE AÑADIDO/MODIFICADO --- */}
            {pub.description && (
              <>
                <h6 className="mt-3 mb-2">Descripción</h6>
                <p className="mb-2" style={{ whiteSpace: "pre-wrap" }}>{pub.description}</p>
              </>
            )}
            {/* --- FIN BLOQUE AÑADIDO/MODIFICADO --- */}

            {/* Renglón 2: Categorías (MOVIDO HACIA ARRIBA) */}
            <h6 className="mt-3 mb-2">Categorías</h6>
            <div className="d-flex flex-wrap gap-1 mb-3">
              {pub.categories?.map(cat => (
                <span key={cat} className="badge bg-secondary-subtle text-secondary border text-capitalize">
                  {cat}
                </span>
              ))}
            </div>

            {/* Renglón 3: Ubicación (ANTES ESTABA EN MEDIO) */}
            <h6 className="mt-3 mb-2">Ubicación</h6>
            <p className="mb-2">
              📍 {pub.address}, {pub.city}, {pub.province}
            </p>

            {/* Renglón 4: Precio */}
            <h6 className="mt-3 mb-2">Precio</h6>
            <p className="mb-2">
              ${pub.cost_per_day} por día
            </p>

            {/* --- INICIO SECCIÓN DE RESEÑAS AÑADIDA --- */}
            <hr />
            <h6 className="mt-3 mb-2">Reseñas</h6>

            {/* Lista de reseñas */}
            <div style={{ maxHeight: 250, overflow: "auto" }}>
              {loading && <div className="text-muted">Cargando…</div>}
              {err && <div className="alert alert-danger">{err}</div>}
              {!loading && !err && list.length === 0 && <div className="text-muted">Sin reseñas todavía.</div>}
              <ul className="list-unstyled mb-0">
                {list.map((r) => (
                  <li key={r.id} className="border rounded-3 p-3 mb-2">
                    <div className="d-flex justify-content-between">
                      <Stars value={r.rating} />
                      <small className="text-muted">{new Date(r.created_at).toLocaleString()}</small>
                    </div>
                    {r.comment && <div className="mt-1">{r.comment}</div>}
                    <small className="text-muted d-block mt-1">por {r.author_username}</small>
                  </li>
                ))}
              </ul>
            </div>

            {/* Formulario para nueva reseña */}
            {isPremium ? (
              <form className="p-3 border-top" onSubmit={submitReview}>
                <div className="row g-2">
                  <div className="col-12 col-md-2">
                    <label className="form-label mb-1">Rating</label>
                    <select className="form-select" value={rating} onChange={(e) => setRating(e.target.value)}>
                      {[5, 4, 3, 2, 1].map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                  <div className="col-12 col-md-8">
                    <label className="form-label mb-1">Comentario (opcional)</label>
                    <input className="form-control" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Contanos tu experiencia" />
                  </div>
                  <div className="col-12 col-md-2 d-flex align-items-end">
                    <button className="btn btn-celeste w-100" type="submit">Publicar</button>
                  </div>
                </div>
              </form>
            ) : (
              <div className="p-3 border-top">
                <div className="alert alert-secondary mb-0">
                  Solo los <strong>usuarios premium</strong> pueden publicar reseñas.
                </div>
              </div>
            )}
            {/* --- FIN SECCIÓN DE RESEÑAS AÑADIDA --- */}

          </div>
        </div>
      </div>
    </div>
  );
}