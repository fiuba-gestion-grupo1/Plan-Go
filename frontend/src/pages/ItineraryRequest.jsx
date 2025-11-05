import React, { useState, useEffect } from 'react';
import ItineraryRequestForm from '../components/ItineraryRequestForm';

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

/* --- UI helpers (COPIADO DE HOME.JSX) --- */
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

export default function ItineraryRequest({ initialView = 'form', me }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [myItineraries, setMyItineraries] = useState([]);
  const [showList, setShowList] = useState(initialView === 'list');
  const [selectedItinerary, setSelectedItinerary] = useState(null);
  const token = localStorage.getItem('token') || '';

  //Estado para el modal de publicación ---
  const [openDetailModal, setOpenDetailModal] = useState(false);
  const [currentPub, setCurrentPub] = useState(null);

  useEffect(() => {
    if (initialView === 'list') {
      fetchMyItineraries();
    }
  }, [initialView]);

  async function fetchMyItineraries() {
    setLoading(true);
    setError('');
    try {
      const data = await request('/api/itineraries/my-itineraries', { token });
      setMyItineraries(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteItinerary(itineraryId) {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este itinerario? Esta acción no se puede deshacer.')) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      await request(`/api/itineraries/${itineraryId}`, {
        method: 'DELETE',
        token
      });

      setSuccessMsg('Itinerario eliminado exitosamente');

      if (selectedItinerary && selectedItinerary.id === itineraryId) {
        setSelectedItinerary(null);
        setShowList(true);
      }

      await fetchMyItineraries();
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (e) {
      setError(e.message || 'Error al eliminar el itinerario');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(payload) {
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const data = await request('/api/itineraries/request', {
        method: 'POST',
        token,
        body: payload
      });

      setSuccessMsg('¡Itinerario generado exitosamente!');
      setSelectedItinerary(data);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (e) {
      setError(e.message || 'Error al solicitar el itinerario');
    } finally {
      setLoading(false);
    }
  }

  function handleViewItineraries() {
    setShowList(true);
    setSelectedItinerary(null);
    fetchMyItineraries();
  }

  function handleNewRequest() {
    setShowList(false);
    setSelectedItinerary(null);
    setError('');
    setSuccessMsg('');
  }

  function handleViewItinerary(itinerary) {
    setSelectedItinerary(itinerary);
    setShowList(false);
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

  async function toggleFavorite(pubId) {
    // Actualiza el estado de favoritos en la lista de itinerarios
    try {
      const data = await request(`/api/publications/${pubId}/favorite`, {
        method: "POST",
        token
      });
      // Actualiza la publicación dentro de selectedItinerary
      setSelectedItinerary(prev => {
        if (!prev) return null;
        return {
          ...prev,
          publications: prev.publications.map(p =>
            p.id === pubId ? { ...p, is_favorite: data.is_favorite } : p
          )
        };
      });
      // Actualiza la publicación en el modal si está abierta
      if (currentPub && currentPub.id === pubId) {
        setCurrentPub(prev => ({ ...prev, is_favorite: data.is_favorite }));
      }
    } catch (e) {
      setError(e.message || "Error al actualizar favorito");
    }
  }

  // === Vista de la lista de itinerarios ===
  if (showList) {
    return (
      <div className="container mt-4">
        <div className="d-flex align-items-center justify-content-between mb-4">
          <h3 className="mb-0">Mis Itinerarios</h3>
          <button className="btn" onClick={handleNewRequest}>
            + Nuevo Itinerario
          </button>
        </div>

        {loading && <div className="alert alert-info">Cargando...</div>}
        {error && <div className="alert alert-danger">{error}</div>}
        {successMsg && <div className="alert alert-success">{successMsg}</div>}

        <div className="row g-4">
          {myItineraries.map((itinerary) => (
            <div className="col-md-6 col-lg-4" key={itinerary.id}>
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <h5 className="card-title mb-0">{itinerary.destination}</h5>
                    {itinerary.status === 'completed' && <span className="badge bg-success">Completado</span>}
                    {itinerary.status === 'pending' && <span className="badge bg-warning text-dark">Pendiente</span>}
                    {itinerary.status === 'failed' && <span className="badge bg-danger">Error</span>}
                  </div>

                  <p className="text-muted small mb-2">
                    {formatDate(itinerary.start_date)} - {formatDate(itinerary.end_date)}
                  </p>

                  <p><strong>Tipo:</strong> {itinerary.trip_type}</p>
                  <p><strong>Presupuesto:</strong> US${itinerary.budget}</p>
                  <p><strong>Personas:</strong> {itinerary.cant_persons}</p>

                  <div className="d-flex gap-2">
                    <button className="btn btn-sm flex-grow-1" onClick={() => handleViewItinerary(itinerary)}>
                      Ver Itinerario
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleDeleteItinerary(itinerary.id)}
                      title="Eliminar itinerario"
                      disabled={loading}
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <div className="card-footer text-muted small">
                  Creado: {new Date(itinerary.created_at).toLocaleString('es-ES')}
                </div>
              </div>
            </div>
          ))}
        </div>

        {!loading && myItineraries.length === 0 && (
          <div className="alert alert-secondary">
            No tienes itinerarios generados aún. ¡Crea tu primer itinerario con IA!
          </div>
        )}
      </div>
    );
  }

  // === Vista de detalle del itinerario ===
  if (selectedItinerary) {
    return (
      <> {/* Fragment para incluir el modal */}
        <div className="container mt-4">
          <div className="d-flex align-items-center justify-content-between mb-4">
            <h3 className="mb-0">Itinerario: {selectedItinerary.destination}</h3>
            <div className="d-flex gap-2">
              <button className="btn btn-outline-secondary" onClick={handleViewItineraries}>
                Mis Itinerarios
              </button>
              <button
                className="btn btn-outline-danger"
                onClick={() => handleDeleteItinerary(selectedItinerary.id)}
                disabled={loading}
              >
                🗑️ Eliminar
              </button>
              <button className="btn btn-celeste" onClick={handleNewRequest}>
                + Nuevo Itinerario
              </button>
            </div>
          </div>

          {error && <div className="alert alert-danger">{error}</div>}
          {successMsg && <div className="alert alert-success">{successMsg}</div>}

          <div className="card shadow-sm mb-4">
            {/* ... (info del itinerario) ... */}
            <div className="card-body">
              <div className="row mb-3">
                <div className="col-md-6">
                  <p><strong>Fechas:</strong> {formatDate(selectedItinerary.start_date)} - {formatDate(selectedItinerary.end_date)}</p>
                  <p><strong>Tipo de viaje:</strong> {selectedItinerary.trip_type}</p>
                  <p><strong>Presupuesto:</strong> US${selectedItinerary.budget}</p>
                  <p><strong>Personas:</strong> {selectedItinerary.cant_persons}</p>
                </div>
                <div className="col-md-6">
                  {selectedItinerary.arrival_time && <p><strong>Hora de llegada:</strong> {selectedItinerary.arrival_time}</p>}
                  {selectedItinerary.departure_time && <p><strong>Hora de salida:</strong> {selectedItinerary.departure_time}</p>}
                  <p>
                    <strong>Estado:</strong>{' '}
                    {selectedItinerary.status === 'completed' && <span className="badge bg-success">Completado</span>}
                    {selectedItinerary.status === 'pending' && <span className="badge bg-warning text-dark">Pendiente</span>}
                    {selectedItinerary.status === 'failed' && <span className="badge bg-danger">Error</span>}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="card shadow-sm">
            {/* ... (itinerario generado por IA) ... */}
            <div className="card-header text-white d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Itinerario Generado por IA</h5>
              <button
                className="btn btn-sm btn-light"
                onClick={() => navigator.clipboard.writeText(selectedItinerary.generated_itinerary || '')}
              >
                📋 Copiar
              </button>
            </div>
            <div className="card-body">
              {selectedItinerary.status === 'completed' ? (
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.8', fontSize: '0.95rem' }}>
                  {selectedItinerary.generated_itinerary}
                </div>
              ) : (
                <div className="alert alert-warning">
                  {selectedItinerary.generated_itinerary || 'No se pudo generar el itinerario'}
                </div>
              )}
            </div>
          </div>

          {/* Publicaciones utilizadas en el itinerario (BLOQUE MODIFICADO) */}
          {selectedItinerary.publications && selectedItinerary.publications.length > 0 && (
            <div className="mt-4">
              <h4 className="mb-3">📍 Lugares incluidos en este itinerario</h4>
              <p className="text-muted mb-3">
                Estos son los lugares de nuestra plataforma que la IA utilizó para crear tu itinerario:
              </p>

              {/* --- GRILLA DE PUBLICACIONES ACTUALIZADA --- */}
              <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
                {selectedItinerary.publications.map((p) => (
                  <div className="col" key={p.id}>
                    <div
                      className="card shadow-sm h-100 border-success"
                      onClick={() => openPublicationDetail(p)}
                      style={{ cursor: "pointer" }}
                    >
                      <div className="card-body pb-0">
                        <div className="d-flex justify-content-between align-items-start">
                          <div className="flex-grow-1">
                            <h5 className="card-title mb-1">{p.place_name}</h5>
                            <small className="text-muted">
                              {p.address}, {p.city}, {p.province}, {p.country}
                            </small>
                            <div className="mt-2 d-flex flex-wrap gap-2">
                              {/* USA EL COMPONENTE RatingBadge */}
                              <RatingBadge avg={p.rating_avg} count={p.rating_count} />
                              {(p.categories || []).map((c) => (
                                <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                              ))}
                            </div>
                          </div>

                          {/* BOTÓN DE FAVORITO */}
                          <button
                            className="btn btn-link p-0 ms-2"
                            onClick={(e) => { e.stopPropagation(); toggleFavorite(p.id); }}
                            style={{ fontSize: "1.5rem", textDecoration: "none" }}
                            title={p.is_favorite ? "Quitar de favoritos" : "Agregar a favoritos"}
                          >
                            {p.is_favorite ? "❤️" : "🤍"}
                          </button>
                        </div>
                      </div>

                      {p.photos?.length ? (
                        <div id={`itin-carousel-${p.id}`} className="carousel slide" data-bs-ride="false">
                          <div className="carousel-inner">
                            {p.photos.map((url, idx) => (
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
                          {/* Controles del carrusel (iguales a Home) */}
                          {p.photos.length > 1 && (
                            <>
                              <button className="carousel-control-prev" type="button" data-bs-target={`#itin-carousel-${p.id}`} data-bs-slide="prev">
                                <span className="carousel-control-prev-icon" aria-hidden="true" />
                              </button>
                              <button className="carousel-control-next" type="button" data-bs-target={`#itin-carousel-${p.id}`} data-bs-slide="next">
                                <span className="carousel-control-next-icon" aria-hidden="true" />
                              </button>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="p-4 text-center text-muted">Sin fotos</div>
                      )}

                      {/* BOTÓN "VER DETALLES" */}
                      <div className="card-footer bg-white d-flex justify-content-between align-items-center">
                        <small className="text-muted">Creado: {new Date(p.created_at).toLocaleString()}</small>
                        <button
                          className="btn btn-sm btn-celeste"
                          onClick={(e) => { e.stopPropagation(); openPublicationDetail(p); }}
                        >
                          Ver Detalles
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* --- RENDER DEL MODAL --- */}
        <PublicationDetailModal
          open={openDetailModal}
          pub={currentPub}
          token={token}
          me={me || {}} // Pasamos 'me' (si existe) o un objeto vacío
          onClose={() => setOpenDetailModal(false)}
          onToggleFavorite={toggleFavorite}
        />
      </>
    );
  }

  // === Vista del formulario de solicitud ===
  return (
    <div className="container mt-4">
      {/* ... (tu vista de formulario no cambia) ... */}
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
            {pub.photos?.length > 0 ? (
              <div id={`carousel-${pub.id}`} className="carousel slide" data-bs-ride="carousel">
                <div className="carousel-inner">
                  {pub.photos.map((img, i) => (
                    <div key={i} className={`carousel-item ${i === 0 ? 'active' : ''}`}>
                      <img src={img} className="d-block w-100 rounded" alt={`Imagen ${i + 1}`}
                        style={{ height: "300px", objectFit: "cover" }} />
                    </div>
                  ))}
                </div>
                {pub.photos.length > 1 && (
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

            {pub.description && (
              <>
                <h6 className="mt-3 mb-2">Descripción</h6>
                <p className="mb-2" style={{ whiteSpace: "pre-wrap" }}>{pub.description}</p>
              </>
            )}

            <h6 className="mt-3 mb-2">Categorías</h6>
            <div className="d-flex flex-wrap gap-1 mb-3">
              {pub.categories?.map(cat => (
                <span key={cat} className="badge bg-secondary-subtle text-secondary border text-capitalize">
                  {cat}
                </span>
              ))}
            </div>

            <h6 className="mt-3 mb-2">Ubicación</h6>
            <p className="mb-2">
              📍 {pub.address}, {pub.city}, {pub.province}
            </p>

            <h6 className="mt-3 mb-2">Precio</h6>
            <p className="mb-2">
              ${pub.cost_per_day} por día
            </p>

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
          </div>
        </div>
      </div>
    </div>
  );
}