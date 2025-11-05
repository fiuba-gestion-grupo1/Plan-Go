import React, { useEffect, useMemo, useRef, useState } from "react";
import CreatePublicationForm from "../components/CreatePublicationForm";
import ItineraryRequestForm from "../components/ItineraryRequestForm";
import "../styles/buttons.css";
import ItineraryRequest from "../pages/ItineraryRequest";

/* Helper fetch */
async function request(path, { method = "GET", token, body, isForm = false } = {}) {
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

/* --- UI helpers --- */
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

/* --- Dropdown multiselect --- */
function useOnClickOutside(ref, handler) {
  useEffect(() => {
    function listener(e) {
      if (!ref.current || ref.current.contains(e.target)) return;
      handler(e);
    }
    document.addEventListener("mousedown", listener);
    return () => document.removeEventListener("mousedown", listener);
  }, [ref, handler]);
}

function MultiCategoryDropdown({ allCats = [], selected = [], onApply, onReload }) {
  const [open, setOpen] = useState(false);
  const [temp, setTemp] = useState(selected);
  const boxRef = useRef(null);

  useEffect(() => { if (open) setTemp(selected); }, [open, selected]);
  useOnClickOutside(boxRef, () => setOpen(false));

  function toggle(c) {
    setTemp(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]);
  }
  function clear() { setTemp([]); }
  function apply() { onApply(temp); setOpen(false); }

  return (
    <div className="position-relative">
      <button
        type="button"
        style={{ borderColor: '#3A92B5', color: '#3A92B5' }}
        className="btn btn-celeste dropdown-toggle"
        onClick={() => { setOpen(o => !o); if (!open && onReload) onReload(); }}
      >
        Categorías
      </button>
      {open && (
        <div
          ref={boxRef}
          className="position-absolute end-0 mt-2 p-3 bg-white border rounded-3 shadow"
          style={{ minWidth: 280, zIndex: 1000, maxHeight: 360, overflow: "auto" }}
        >
          <div className="d-flex align-items-center justify-content-between mb-2">
            <div className="fw-semibold text-muted small">Tipo de categoría</div>
            <button className="btn btn-sm btn-link" type="button" onClick={onReload} title="Actualizar lista">↻</button>
          </div>
          <ul className="list-unstyled mb-3" style={{ columnGap: 24 }}>
            {allCats.length === 0 && <li className="text-muted small">Sin categorías aún.</li>}
            {allCats.map((c) => (
              <li key={c} className="form-check mb-2">
                <input id={`cat-${c}`} type="checkbox" className="form-check-input" checked={temp.includes(c)} onChange={() => toggle(c)} />
                <label className="form-check-label ms-1 text-capitalize" htmlFor={`cat-${c}`}>{c}</label>
              </li>
            ))}
          </ul>
          <div className="d-flex justify-content-between gap-2">
            <button className="btn btn-outline-secondary" type="button" onClick={clear}>Limpiar</button>
            <button className="btn btn-outline-custom" style={{ borderColor: '#3A92B5', color: '#3A92B5' }} type="button" onClick={apply}>Ver resultados</button>
          </div>
        </div>
      )}
    </div>
  );
}

function ReviewsModal({ open, pub, token, me, onClose }) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const isPremium = me?.role === "premium" || me?.username === "admin"; // si no querés que admin publique, quitá la segunda condición

  useEffect(() => {
    if (!open || !pub?.id) return;
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
  }, [open, pub?.id]);

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
      const rows = await request(`/api/publications/${pub.id}/reviews`);
      setList(rows);
    } catch (e) {
      alert(`Error creando reseña: ${e.message}`);
    }
  }

  if (!open) return null;

  return (
    <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-end align-items-md-center justify-content-center" style={{ background: "rgba(0,0,0,.4)", zIndex: 1050 }}>
      <div className="bg-white rounded-3 shadow-lg border w-100" style={{ maxWidth: 720, maxHeight: "90vh" }}>
        <div className="p-3 border-bottom d-flex align-items-center justify-content-between">
          <div>
            <h5 className="mb-1">Reseñas — {pub?.place_name}</h5>
            <RatingBadge avg={pub?.rating_avg} count={pub?.rating_count} />
          </div>
          <button className="btn btn-sm btn-outline-secondary" onClick={onClose}>Cerrar</button>
        </div>

        <div className="p-3" style={{ overflow: "auto", maxHeight: 350 }}>
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
                <button className="btn  w-100" type="submit">Publicar</button>
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
  );
}

/* --- NUEVO BLOQUE: Configurar preferencias --- */
function PreferencesBox({ token }) {
  const [prefs, setPrefs] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await request("/api/preferences", { token });
        setPrefs(data);
      } catch {
        setPrefs({});
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  async function savePreferences() {
    setSaving(true);
    try {
      await request("/api/preferences", { method: "PUT", token, body: prefs });
      alert("Preferencias guardadas correctamente");
    } catch (e) {
      alert("Error guardando preferencias: " + e.message);
    } finally {
      setSaving(false);
    }
  }

  function toggleList(key, val) {
    const list = prefs[key] || [];
    const updated = list.includes(val)
      ? list.filter((v) => v !== val)
      : [...list, val];
    setPrefs({ ...prefs, [key]: updated });
  }

  if (loading) return <div className="text-muted">Cargando preferencias…</div>;

  return (
    <div className="border rounded-3 p-3 bg-white shadow-sm mb-4">
      <h5 className="mb-3">Configurar preferencias</h5>

      <div className="row g-2 mb-3">
        <div className="col-md-3">
          <label className="form-label">Presupuesto mín. (USD)</label>
          <input type="number" className="form-control"
            value={prefs.budget_min || ""}
            onChange={(e) => setPrefs({ ...prefs, budget_min: Number(e.target.value) || null })} />
        </div>
        <div className="col-md-3">
          <label className="form-label">Presupuesto máx. (USD)</label>
          <input type="number" className="form-control"
            value={prefs.budget_max || ""}
            onChange={(e) => setPrefs({ ...prefs, budget_max: Number(e.target.value) || null })} />
        </div>
        <div className="col-md-3">
          <label className="form-label">Duración mín. (días)</label>
          <input type="number" className="form-control"
            value={prefs.duration_min_days || ""}
            onChange={(e) => setPrefs({ ...prefs, duration_min_days: Number(e.target.value) || null })} />
        </div>
        <div className="col-md-3">
          <label className="form-label">Duración máx. (días)</label>
          <input type="number" className="form-control"
            value={prefs.duration_max_days || ""}
            onChange={(e) => setPrefs({ ...prefs, duration_max_days: Number(e.target.value) || null })} />
        </div>
      </div>

      <div className="mb-3">
        <strong>Climas:</strong>{" "}
        {["templado", "frio", "tropical", "seco"].map(v => (
          <button key={v} className={`btn btn-sm me-2 mb-2 ${prefs.climates?.includes(v) ? "btn-primary" : "btn-outline-primary"}`}
            onClick={() => toggleList("climates", v)}>{v}</button>
        ))}
      </div>

      <div className="mb-3">
        <strong>Actividades:</strong>{" "}
        {["playa", "montaña", "ciudad", "gastronomía", "historia", "noche"].map(v => (
          <button key={v} className={`btn btn-sm me-2 mb-2 ${prefs.activities?.includes(v) ? "btn-success" : "btn-outline-success"}`}
            onClick={() => toggleList("activities", v)}>{v}</button>
        ))}
      </div>

      <div className="mb-3">
        <strong>Continentes:</strong>{" "}
        {["américa", "europa", "asia", "áfrica", "oceanía"].map(v => (
          <button key={v} className={`btn btn-sm me-2 mb-2 ${prefs.continents?.includes(v) ? "btn-secondary" : "btn-outline-secondary"}`}
            onClick={() => toggleList("continents", v)}>{v}</button>
        ))}
      </div>

      <button className="btn btn-dark" disabled={saving} onClick={savePreferences}>
        {saving ? "Guardando..." : "Guardar preferencias"}
      </button>
    </div>
  );
}

/* --- MAIN HOME --- */
export default function Home({ me, view = "publications" }) {
  const [pubs, setPubs] = useState([]);
  const [myPubs, setMyPubs] = useState([]);
  const [favPubs, setFavPubs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [subView, setSubView] = useState(null);
  const [selectedItinerary, setSelectedItinerary] = useState(null);
  const [myItineraries, setMyItineraries] = useState([]);
  const [successMsg, setSuccessMsg] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const token = useMemo(() => localStorage.getItem("token") || "", []);
  // leer ?pub=ID una sola vez
  const [paramPubId] = useState(() => {
    try {
      const id = new URL(window.location.href).searchParams.get("pub");
      return id ? Number(id) : null;
    } catch {
      return null;
    }
  });

  const [cats, setCats] = useState([]);
  const [allCats, setAllCats] = useState([]);

  // const [open, setOpen] = useState(false);
  // const [current, setCurrent] = useState(null);
  const [openDetailModal, setOpenDetailModal] = useState(false); // Podrías renombrar 'open' a 'openDetailModal' por claridad
  const [currentPub, setCurrentPub] = useState(null);
  const [selectedPub, setSelectedPub] = useState(null);

  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

  async function reloadCats() {
    try {
      const list = await request("/api/categories");
      setAllCats(list);
    } catch {
      // si no existe endpoint, ignoramos
      setAllCats([]);
    }
  }

  useEffect(() => { reloadCats(); }, []);

  // Construye endpoint según búsqueda o categorías
  function buildPublicationsEndpoint(query, categories) {
    if (query && query.trim().length >= 2) {
      return `/api/publications/search?q=${encodeURIComponent(query.trim())}`;
    }
    const qs = categories?.length ? `?category=${encodeURIComponent(categories.join(","))}` : "";
    return `/api/publications/public${qs}`;
  }

  async function fetchPublications(query = "", categories = cats) {
    setLoading(true);
    setError("");
    try {
      const endpoint = buildPublicationsEndpoint(query, categories);
      const data = await request(endpoint, { token });
      setPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // carga inicial según la vista activa
  useEffect(() => {
    if (view === 'publications' && !subView) {
      fetchPublications(searchQuery, cats);
    } else if (view === 'my-publications' && !subView) {
      fetchMySubmissions();
    } else if (view === 'favorites' && !subView) {
      fetchFavorites();
    } else if (view === 'my-itineraries' && !subView) {
      fetchMyItineraries();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, view, JSON.stringify(cats)]);

  // Si viene ?pub=ID en la URL, abre automáticamente esa publicación cuando hay datos
  useEffect(() => {
    if (!paramPubId) return;
    if (!Array.isArray(pubs) || pubs.length === 0) return;
    const found = pubs.find(p => p.id === paramPubId);
    if (found) {
      setCurrentPub(found);
      setOpenDetailModal(true);
      try {
        const url = new URL(window.location.href);
        url.searchParams.delete("pub");
        window.history.replaceState({}, "", url.pathname);
      } catch { }
    }
  }, [paramPubId, pubs]);

  function openReviews(p) { setCurrent(p); setOpen(true); }

  async function fetchMySubmissions() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/publications/my-submissions", { token });
      setMyPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchFavorites() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/publications/favorites", { token });
      setFavPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function toggleFavorite(pubId) {
    try {
      const data = await request(`/api/publications/${pubId}/favorite`, {
        method: "POST",
        token
      });
      setPubs(prevPubs =>
        prevPubs.map(p =>
          p.id === pubId ? { ...p, is_favorite: data.is_favorite } : p
        )
      );
    } catch (e) {
      setError(e.message);
    }
  }

  async function updateFavoriteStatus(pubId, newStatus) {
    try {
      await request(`/api/publications/favorites/${pubId}/status`, {
        method: "PUT",
        token,
        body: { status: newStatus },
      });

      // Refrescamos solo el array de favoritos en memoria
      setFavPubs(prev =>
        prev.map(p => p.id === pubId ? { ...p, favorite_status: newStatus } : p)
      );
    } catch (e) {
      setError(e.message || "Error al actualizar el estado del favorito");
    }
  }

  const [deletionReasonModal, setDeletionReasonModal] = useState(false);
  const [deletionReasonPubId, setDeletionReasonPubId] = useState(null);
  const [deletionReason, setDeletionReason] = useState("");

  async function requestDeletion(pubId) {
    setDeletionReasonPubId(pubId);
    setDeletionReason("");
    setDeletionReasonModal(true);
  }

  async function submitDeletionRequest() {
    if (!deletionReasonPubId) return;
    if (!deletionReason.trim()) {
      setError("Por favor, escribe un motivo para solicitar la eliminación.");
      return;
    }
    try {
      await request(`/api/publications/${deletionReasonPubId}/request-deletion`, {
        method: "POST",
        token,
        body: { reason: deletionReason }
      });
      setSuccessMsg("Solicitud de eliminación enviada. Será revisada por un administrador.");
      setMyPubs(prevPubs =>
        prevPubs.map(p =>
          p.id === deletionReasonPubId ? { ...p, has_pending_deletion: true } : p
        )
      );
      setDeletionReasonModal(false);
      setDeletionReasonPubId(null);
      setDeletionReason("");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (e) {
      setError(e.message);
    }
  }

  async function fetchMyItineraries() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/itineraries/my-itineraries", { token });
      setMyItineraries(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleItinerarySubmit(payload) {
    setLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      const data = await request("/api/itineraries/request", {
        method: "POST",
        token,
        body: payload
      });

      setSuccessMsg("¡Itinerario generado exitosamente!");
      setSelectedItinerary(data);
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (e) {
      setError(e.message || "Error al solicitar el itinerario");
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteItinerary(itineraryId) {
    if (!window.confirm("¿Estás seguro de que deseas eliminar este itinerario? Esta acción no se puede deshacer.")) {
      return;
    }

    setLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      await request(`/api/itineraries/${itineraryId}`, {
        method: "DELETE",
        token
      });

      setSuccessMsg("Itinerario eliminado exitosamente");

      if (selectedItinerary && selectedItinerary.id === itineraryId) {
        setSelectedItinerary(null);
      }

      await fetchMyItineraries();
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (e) {
      setError(e.message || "Error al eliminar el itinerario");
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(query) {
    setSearchQuery(query);
    fetchPublications(query, cats);
  }

  async function handleCreateSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    const form = e.currentTarget;
    const fd = new FormData(form);

    // Convertir campos numéricos de string a number
    const costPerDay = fd.get('cost_per_day');
    const durationDays = fd.get('duration_days');

    if (costPerDay && costPerDay.trim() !== '') {
      fd.set('cost_per_day', parseFloat(costPerDay));
    } else {
      fd.delete('cost_per_day');
    }

    if (durationDays && durationDays.trim() !== '') {
      fd.set('duration_days', parseInt(durationDays, 10));
    } else {
      fd.delete('duration_days');
    }

    // Debug: mostrar qué se está enviando
    console.log("Datos del formulario:");
    for (let pair of fd.entries()) {
      console.log(pair[0] + ': ' + pair[1]);
    }

    const files = form.photos.files || [];
    if (files.length > 4) {
      setError("Máximo 4 fotos por publicación.");
      return;
    }
    setLoading(true);
    try {
      const result = await request("/api/publications/submit", {
        method: "POST",
        token,
        body: fd,
        isForm: true,
      });
      console.log("Respuesta del servidor:", result);
      setSuccessMsg("¡Publicación enviada! Será revisada por un administrador.");
      form.reset();
      setTimeout(() => {
        setSubView(null);
        setSuccessMsg("");
      }, 2000);
    } catch (e) {
      console.error("Error completo:", e);
      setError(e.message || "Error al enviar la publicación");
    } finally {
      setLoading(false);
    }
  }

  // Mostrar formulario de crear publicación
  if (subView === 'create-publication') {
    return (
      <CreatePublicationForm
        onSubmit={handleCreateSubmit}
        onCancel={() => {
          setSubView(null);
          setError("");
          setSuccessMsg("");
        }}
        loading={loading}
        error={error}
        successMsg={successMsg}
      />
    );
  }

  // Vista de Mis Publicaciones
  if (view === 'my-publications' && !subView) {
    return (
      <>
        <MySubmissionsView
          pubs={myPubs}
          loading={loading}
          error={error}
          successMsg={successMsg}
          onLoad={fetchMySubmissions}
          onRequestDeletion={requestDeletion}
          setSubView={setSubView}
        />

        {/* Modal de solicitud de eliminación */}
        {deletionReasonModal && (
          <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
            style={{ background: "rgba(0,0,0,.4)", zIndex: 1051 }}>
            <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 500, width: "90%" }}>
              <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Solicitar Eliminación de Publicación</h5>
                <button className="btn-close" onClick={() => setDeletionReasonModal(false)}></button>
              </div>
              <div className="p-3">
                <p className="text-muted mb-3">
                  Un administrador revisará tu solicitud. Por favor, cuéntale por qué deseas eliminar esta publicación.
                </p>
                <form onSubmit={(e) => { e.preventDefault(); submitDeletionRequest(); }}>
                  <div className="mb-3">
                    <label className="form-label">Motivo de la eliminación</label>
                    <textarea
                      className="form-control"
                      rows="4"
                      placeholder="Escribe el motivo..."
                      value={deletionReason}
                      onChange={(e) => setDeletionReason(e.target.value)}
                      maxLength="500"
                    ></textarea>
                    <small className="text-muted d-block mt-1">
                      {deletionReason.length}/500 caracteres
                    </small>
                  </div>
                  <div className="d-flex gap-2">
                    <button
                      type="button"
                      className="btn btn-outline-secondary flex-grow-1"
                      onClick={() => setDeletionReasonModal(false)}
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="btn btn-danger flex-grow-1"
                      disabled={!deletionReason.trim()}
                    >
                      Solicitar Eliminación
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Vista de Favoritos
  if (view === 'favorites' && !subView) {
    return (
      <FavoritesView
        pubs={favPubs}
        loading={loading}
        error={error}
        onLoad={fetchFavorites}
        onToggleFavorite={async (pubId) => {
          await toggleFavorite(pubId);
          fetchFavorites();
        }}
        onUpdateStatus={updateFavoriteStatus}  // ✅ sin tipos
      />
    );
  }


  // Vista de Configurar Preferencias
  if (view === 'preferences') {
    return <PreferencesBox token={token} />;
  }

  // Vista del formulario de itinerario o del itinerario seleccionado
  if (view === 'itinerary' || selectedItinerary) {
    const formatDate = (dateStr) => {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    };

    // Vista de detalle de un itinerario
    if (selectedItinerary) {
      return (
        <div className="container mt-4">
          <div className="d-flex align-items-center justify-content-between mb-4">
            <h3 className="mb-0">Itinerario: {selectedItinerary.destination}</h3>
            <div className="d-flex gap-2">
              <button
                className="btn btn-outline-secondary"
                onClick={() => {
                  setSelectedItinerary(null);
                  setError("");
                  setSuccessMsg("");
                }}
              >
                Volver
              </button>
              <button
                className="btn btn-outline-danger"
                onClick={() => handleDeleteItinerary(selectedItinerary.id)}
                disabled={loading}
              >
                🗑️ Eliminar
              </button>
            </div>
          </div>

          {error && <div className="alert alert-danger" role="alert">{error}</div>}
          {successMsg && <div className="alert alert-success" role="alert">{successMsg}</div>}

          <div className="card shadow-sm mb-4">
            <div className="card-body">
              <div className="row mb-3">
                <div className="col-md-6">
                  <p><strong>📅 Fechas:</strong> {formatDate(selectedItinerary.start_date)} - {formatDate(selectedItinerary.end_date)}</p>
                  <p><strong>🎯 Tipo de viaje:</strong> {selectedItinerary.trip_type}</p>
                  <p><strong>💰 Presupuesto:</strong> US${selectedItinerary.budget}</p>
                  <p><strong>👥 Personas:</strong> {selectedItinerary.cant_persons}</p>
                </div>
                <div className="col-md-6">
                  {selectedItinerary.arrival_time && (
                    <p><strong>🛬 Hora de llegada:</strong> {selectedItinerary.arrival_time}</p>
                  )}
                  {selectedItinerary.departure_time && (
                    <p><strong>🛫 Hora de salida:</strong> {selectedItinerary.departure_time}</p>
                  )}
                  <p>
                    <strong>Estado:</strong>{' '}
                    {selectedItinerary.status === 'completed' && (
                      <span className="badge bg-success">Completado</span>
                    )}
                    {selectedItinerary.status === 'pending' && (
                      <span className="badge bg-warning text-dark">Pendiente</span>
                    )}
                    {selectedItinerary.status === 'failed' && (
                      <span className="badge bg-danger">Error</span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="card shadow-sm">
            <div className="card-header bg-info text-white d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Itinerario Generado por IA</h5>
              <button
                className="btn btn-sm btn-light"
                onClick={() => {
                  navigator.clipboard.writeText(selectedItinerary.generated_itinerary || '');
                  alert('Itinerario copiado al portapapeles');
                }}
              >
                📋 Copiar
              </button>
            </div>
            <div className="card-body">
              {selectedItinerary.status === 'completed' ? (
                <div style={{
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                  lineHeight: '1.8',
                  fontSize: '0.95rem',
                  color: '#333'
                }}>
                  {selectedItinerary.generated_itinerary}
                </div>
              ) : (
                <div className="alert alert-warning">
                  {selectedItinerary.generated_itinerary || 'No se pudo generar el itinerario'}
                </div>
              )}
            </div>
          </div>

          {/* Publicaciones utilizadas en el itinerario */}
          {selectedItinerary.publications && selectedItinerary.publications.length > 0 && (
            <div className="mt-4">
              <h4 className="mb-3">📍 Lugares incluidos en este itinerario</h4>
              <p className="text-muted mb-3">
                Estos son los lugares de nuestra plataforma que la IA utilizó para crear tu itinerario:
              </p>
              <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
                {selectedItinerary.publications.map((p) => (
                  <div className="col" key={p.id}>
                    <div className="card shadow-sm h-100 border-success">
                      <div className="card-body pb-0">
                        <div className="d-flex justify-content-between align-items-start">
                          <div className="flex-grow-1">
                            <h5 className="card-title mb-1">{p.place_name}</h5>
                            <small className="text-muted">
                              {p.address}, {p.city}, {p.province}, {p.country}
                            </small>
                            <div className="mt-2 d-flex flex-wrap gap-2">
                              <RatingBadge avg={p.rating_avg} count={p.rating_count} />
                              {(p.categories || []).map((c) => (
                                <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                              ))}
                            </div>
                          </div>

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
                          {p.photos.length > 1 && (
                            <>
                              <button className="carousel-control-prev" type="button" data-bs-target={`#itin-carousel-${p.id}`} data-bs-slide="prev" style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }} aria-label="Anterior" title="Anterior">
                                <span className="carousel-control-prev-icon" aria-hidden="true" />
                                <span className="visually-hidden">Anterior</span>
                              </button>
                              <button className="carousel-control-next" type="button" data-bs-target={`#itin-carousel-${p.id}`} data-bs-slide="next" style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }} aria-label="Siguiente" title="Siguiente">
                                <span className="carousel-control-next-icon" aria-hidden="true" />
                                <span className="visually-hidden">Siguiente</span>
                              </button>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="p-4 text-center text-muted">Sin fotos</div>
                      )}

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

          <div className="alert alert-info mt-4">
            <strong>💡 Tip:</strong> Usa el botón "📋 Copiar" para copiar todo el itinerario y pegarlo donde necesites.
          </div>
        </div>
      );
    }

    // Vista del formulario de solicitud
    return (
      <div className="container mt-4">
        <div className="d-flex align-items-center justify-content-between mb-4">
          <h3 className="mb-0">Solicitar Itinerario con IA</h3>
        </div>

        {error && <div className="alert alert-danger" role="alert">{error}</div>}
        {successMsg && <div className="alert alert-success" role="alert">{successMsg}</div>}

        <div className="row justify-content-center">
          <div className="col-lg-10">
            <ItineraryRequestForm
              onSubmit={handleItinerarySubmit}
              isLoading={loading}
            />
          </div>
        </div>
      </div>
    );
  }

  // Vista de lista de itinerarios
  if (view === 'my-itineraries') {
    const formatDate = (dateStr) => {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    };

    // Agregar aquí la nueva condición para 'itinerary'
    if (view === 'itinerary') {
      return (
        <ItineraryRequest
          initialView="form"
          me={me}
          token={token}
        />
      );
    }

    return (
      <div className="container mt-4">
        <div className="d-flex align-items-center justify-content-between mb-4">
          <h3 className="mb-0"> Mis Itinerarios</h3>
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
                    {itinerary.status === 'completed' && (
                      <span className="badge bg-success">Completado</span>
                    )}
                    {itinerary.status === 'pending' && (
                      <span className="badge bg-warning text-dark">Pendiente</span>
                    )}
                    {itinerary.status === 'failed' && (
                      <span className="badge bg-danger">Error</span>
                    )}
                  </div>

                  <p className="text-muted small mb-2">
                    {formatDate(itinerary.start_date)} - {formatDate(itinerary.end_date)}
                  </p>

                  <p className="mb-2">
                    <strong>Tipo:</strong> {itinerary.trip_type}
                  </p>

                  <p className="mb-2">
                    <strong>Presupuesto:</strong> US${itinerary.budget}
                  </p>

                  <p className="mb-3">
                    <strong>Personas:</strong> {itinerary.cant_persons}
                  </p>

                  <div className="d-flex gap-2">
                    <button
                      className="btn btn-sm btn-outline-custom flex-grow-1"
                      onClick={() => {
                        setSelectedItinerary(itinerary);
                      }}
                    >
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

  function handleSearchSubmit(e) {
    e.preventDefault();
    const searchValue = e.target.search.value.trim();
    handleSearch(searchValue);
  }

  // Vista principal de publicaciones
  return (
    <div className="container mt-4">
      {/* Hero */}
      <div className="p-3 mb-3 bg-light rounded-3">
        <div className="container-fluid py-2">
          <h4 className="fw-bold mb-1">¡Bienvenido a Plan&Go, {me.username}!</h4>
          <p className="small mb-0 text-muted">Usá los filtros para encontrar actividades/lugares y mirá las reseñas antes de decidir.</p>
        </div>
      </div>

      <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
        <h3 className="mb-0">Publicaciones</h3>
        <div className="d-flex align-items-center gap-2 flex-wrap">
          <MultiCategoryDropdown
            allCats={allCats}
            selected={cats}
            onApply={(sel) => { setCats(sel); }}
            onReload={reloadCats}
          />

        </div>
      </div>

      {/* Búsqueda */}
      <form className="d-flex mt-3" onSubmit={handleSearchSubmit}>
        <input
          className="form-control"
          type="search"
          name="search"
          defaultValue={searchQuery}
          placeholder="Buscar por lugar, país, ciudad, clima, actividades, descripción..."
          aria-label="Buscar"
        />
      </form>

      {searchQuery && (
        <div className="alert alert-info d-flex justify-content-between align-items-center mt-3" role="alert">
          <span>
            <strong>Búsqueda:</strong> "{searchQuery}" - {pubs.length} resultado{pubs.length !== 1 ? "s" : ""} encontrado{pubs.length !== 1 ? "s" : ""}
          </span>
          <button
            className="btn btn-sm btn-outline-secondary"
            onClick={() => handleSearch("")}
          >
            Limpiar
          </button>
        </div>
      )}

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}

      {/* --- UNICA GRILLA DE PUBLICACIONES (reemplaza los bloques duplicados) --- */}
      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div
              className="card shadow-sm h-100"
              onClick={() => openPublicationDetail(p)}
              style={{ cursor: "pointer" }}
            >
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted">📍 {p.address ? `${p.address}, ` : ""}{p.city}, {p.province}{p.country ? `, ${p.country}` : ""}</small>

                    <div className="mt-2">
                      {/* Renglón 1: Reseñas */}
                      <div className="mb-2">
                        <RatingBadge avg={p.rating_avg} count={p.rating_count} />
                      </div>

                      {/* Renglón 2: Categorías */}
                      <div className="d-flex flex-wrap gap-1">
                        {(p.categories || []).map((c) => (
                          <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                        ))}
                      </div>
                    </div>

                    <p className="card-text mt-2 mb-0">
                      <span className="text-success fw-bold">${p.cost_per_day}</span>
                    </p>
                  </div>

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
                <div id={`home-carousel-${p.id}`} className="carousel slide" data-bs-ride="false">
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

                  {p.photos.length > 1 && (
                    <>
                      <button className="carousel-control-prev" type="button" data-bs-target={`#home-carousel-${p.id}`} data-bs-slide="prev">
                        <span className="carousel-control-prev-icon" aria-hidden="true" />
                      </button>
                      <button className="carousel-control-next" type="button" data-bs-target={`#home-carousel-${p.id}`} data-bs-slide="next">
                        <span className="carousel-control-next-icon" aria-hidden="true" />
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center text-muted">Sin fotos</div>
              )}

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

      {/* Modal de detalles */}
      <PublicationDetailModal
        open={openDetailModal}
        pub={currentPub}
        token={token}
        me={me}
        onClose={() => setOpenDetailModal(false)}
        onToggleFavorite={toggleFavorite}
      />

      {/* Modal de solicitud de eliminación */}
      {deletionReasonModal && (
        <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{ background: "rgba(0,0,0,.4)", zIndex: 1051 }}>
          <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 500, width: "90%" }}>
            <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Solicitar Eliminación de Publicación</h5>
              <button className="btn-close" onClick={() => setDeletionReasonModal(false)}></button>
            </div>
            <div className="p-3">
              <p className="text-muted mb-3">
                Un administrador revisará tu solicitud. Por favor, cuéntale por qué deseas eliminar esta publicación.
              </p>
              <form onSubmit={(e) => { e.preventDefault(); submitDeletionRequest(); }}>
                <div className="mb-3">
                  <label className="form-label">Motivo de la eliminación</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    placeholder="Escribe el motivo..."
                    value={deletionReason}
                    onChange={(e) => setDeletionReason(e.target.value)}
                    maxLength="500"
                  ></textarea>
                  <small className="text-muted d-block mt-1">
                    {deletionReason.length}/500 caracteres
                  </small>
                </div>
                <div className="d-flex gap-2">
                  <button
                    type="button"
                    className="btn btn-outline-secondary flex-grow-1"
                    onClick={() => setDeletionReasonModal(false)}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-danger flex-grow-1"
                    disabled={!deletionReason.trim()}
                  >
                    Solicitar Eliminación
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MySubmissionsView({ pubs, loading, error, successMsg, onLoad, onRequestDeletion, setSubView }) {
  React.useEffect(() => { onLoad(); }, []);

  const [openDetailModal, setOpenDetailModal] = React.useState(false);
  const [currentPub, setCurrentPub] = React.useState(null);
  const token = React.useMemo(() => localStorage.getItem("token") || "", []);

  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

  const getStatusBadge = (status) => {
    if (status === "approved") return <span className="badge bg-success">Aprobada</span>;
    if (status === "pending") return <span className="badge bg-warning text-dark">Pendiente</span>;
    if (status === "rejected") return <span className="badge bg-danger">Rechazada</span>;
    if (status === "deleted") return <span className="badge bg-dark">Eliminada</span>;
    return <span className="badge bg-secondary">{status}</span>;
  };

  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-4">
        <h3 className="mb-0">Mis Publicaciones</h3>
        <div className="d-flex align-items-center gap-2 flex-wrap">
          <button
            className="btn btn-celeste"
            style={{ borderColor: '#3A92B5', color: '#3A92B5' }}
            onClick={() => setSubView('create-publication')}
          >
            + Agregar Publicación
          </button>

        </div>
      </div>

      {loading && <div className="alert alert-info">Cargando...</div>}
      {error && <div className="alert alert-danger">{error}</div>}
      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div
              className="card shadow-sm h-100"
              onClick={() => openPublicationDetail(p)}
              style={{ cursor: "pointer" }}
            >
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted">📍 {p.address ? `${p.address}, ` : ""}{p.city}, {p.province}{p.country ? `, ${p.country}` : ""}</small>

                    <div className="mt-2">
                      {/* Renglón 1: Reseñas */}
                      <div className="mb-2">
                        <RatingBadge avg={p.rating_avg} count={p.rating_count} />
                      </div>

                      {/* Renglón 2: Categorías */}
                      <div className="d-flex flex-wrap gap-1">
                        {(p.categories || []).map((c) => (
                          <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                        ))}
                      </div>
                    </div>

                    <p className="card-text mt-2 mb-0">
                      <span className="text-success fw-bold">${p.cost_per_day}</span>
                    </p>
                  </div>

                  <div className="d-flex flex-column align-items-end gap-2 ms-2">
                    {getStatusBadge(p.status)}
                    {p.status === "approved" && !p.has_pending_deletion && (
                      <div className="dropdown">
                        <button
                          className="btn btn-sm btn-link text-muted p-0"
                          data-bs-toggle="dropdown"
                          aria-expanded="false"
                          title="Más acciones"
                          onClick={(e) => e.stopPropagation()}
                        >
                          ⋯
                        </button>
                        <ul className="dropdown-menu dropdown-menu-end">
                          <li>
                            <button
                              className="dropdown-item text-danger"
                              onClick={(e) => { e.stopPropagation(); onRequestDeletion(p.id); }}
                            >
                              Solicitar eliminación
                            </button>
                          </li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {p.photos?.length ? (
                <div id={`my-carousel-${p.id}`} className="carousel slide" data-bs-ride="false">
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

                  {p.photos.length > 1 && (
                    <>
                      <button
                        className="carousel-control-prev"
                        type="button"
                        data-bs-target={`#my-carousel-${p.id}`}
                        data-bs-slide="prev"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                      >
                        <span className="carousel-control-prev-icon" />
                      </button>
                      <button
                        className="carousel-control-next"
                        type="button"
                        data-bs-target={`#my-carousel-${p.id}`}
                        data-bs-slide="next"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                      >
                        <span className="carousel-control-next-icon" />
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center text-muted">Sin fotos</div>
              )}

              <div className="card-footer bg-white">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <small className="text-muted">Enviado: {new Date(p.created_at).toLocaleString()}</small>
                  <button
                    className="btn btn-sm btn-celeste"
                    onClick={(e) => { e.stopPropagation(); openPublicationDetail(p); }}
                  >
                    Ver Detalles
                  </button>
                </div>

                {p.status === "rejected" && (
                  <small className="text-danger d-block mt-1">
                    ❌ Esta publicación fue rechazada por un administrador.
                    {p.rejection_reason && (
                      <div className="mt-1 fst-italic">
                        <strong>Motivo:</strong> {p.rejection_reason}
                      </div>
                    )}
                  </small>
                )}
                {p.status === "deleted" && (
                  <small className="text-dark d-block mt-1">
                    🗑️ Esta publicación fue eliminada por un administrador.
                    {p.rejection_reason && (
                      <div className="mt-1 fst-italic">
                        <strong>Motivo:</strong> {p.rejection_reason}
                      </div>
                    )}
                  </small>
                )}
                {p.status === "pending" && (
                  <small className="text-warning d-block mt-1">
                    ⏳ En revisión por un administrador.
                  </small>
                )}
                {p.has_pending_deletion && (
                  <small className="text-info d-block mt-1">
                    🕒 Solicitud de eliminación pendiente de aprobación.
                  </small>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">
          No has enviado ninguna publicación aún.
        </div>
      )}

      {/* Modal de detalles */}
      <PublicationDetailModal
        open={openDetailModal}
        pub={currentPub}
        token={token}
        me={{}}
        onClose={() => setOpenDetailModal(false)}
        onToggleFavorite={() => { }}
      />
    </div>
  );
}

function FavoritesView({
  pubs,
  loading,
  error,
  onLoad,
  onToggleFavorite,
  onUpdateStatus,
}) {
  const [openDetailModal, setOpenDetailModal] = React.useState(false);
  const [currentPub, setCurrentPub] = React.useState(null);
  const token = React.useMemo(() => localStorage.getItem("token") || "", []);

  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

  React.useEffect(() => { onLoad(); }, []);

  const [filter, setFilter] = React.useState("all");
  const shown = React.useMemo(
    () => pubs.filter(p => filter === "all" ? true : (p.favorite_status || "pending") === filter),
    [pubs, filter]
  );

  return (
    <div className="container-fluid py-4">
      <div className="d-flex align-items-center justify-content-between mb-4">
        <h3 className="mb-0">Mis Favoritos</h3>
        <div className="btn-group btn-group-sm" role="group" aria-label="Filtro favoritos">
          {[
            { key: "all", label: "Todos" },
            { key: "pending", label: "⏳ Pendientes" },
            { key: "done", label: "✅ Realizados" }
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className="btn"
              style={{
                borderColor: "#3A92B5",
                color: filter === key ? "white" : "#3A92B5",
                backgroundColor: filter === key ? "#3A92B5" : "transparent",
                borderWidth: "1.5px",
                fontWeight: 500,
                borderRadius:
                  key === "all"
                    ? "8px 0 0 8px"
                    : key === "done"
                      ? "0 8px 8px 0"
                      : "0",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = "#3A92B5";
                e.target.style.color = "white";
              }}
              onMouseLeave={(e) => {
                if (filter !== key) {
                  e.target.style.backgroundColor = "transparent";
                  e.target.style.color = "#3A92B5";
                }
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {loading && <div className="alert alert-info">Cargando...</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
        {shown.map((p) => {
          const status = p.favorite_status || "pending";
          return (
            <div className="col" key={p.id}>
              <div
                className="card shadow-sm h-100"
                onClick={() => openPublicationDetail(p)}
                style={{ cursor: "pointer" }}
              >
                <div className="card-body pb-0">
                  <div className="d-flex justify-content-between align-items-start">
                    <div className="flex-grow-1">
                      <h5 className="card-title mb-1">{p.place_name}</h5>
                      <small className="text-muted">📍 {p.address ? `${p.address}, ` : ""}{p.city}, {p.province}{p.country ? `, ${p.country}` : ""}</small>

                      <div className="mt-2">
                        {/* Renglón 1: Reseñas */}
                        <div className="mb-2">
                          <RatingBadge avg={p.rating_avg} count={p.rating_count} />
                        </div>

                        {/* Renglón 2: Categorías */}
                        <div className="d-flex flex-wrap gap-1">
                          {(p.categories || []).map((c) => (
                            <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                          ))}
                        </div>
                      </div>

                      <p className="card-text mt-2 mb-0">
                        <span className="text-success fw-bold">${p.cost_per_day}</span>
                      </p>
                    </div>

                    <button
                      className="btn btn-link p-0 ms-2"
                      onClick={(e) => { e.stopPropagation(); onToggleFavorite(p.id); }}
                      style={{ fontSize: "1.5rem", textDecoration: "none" }}
                      title="Quitar de favoritos"
                    >
                      ❤️
                    </button>
                  </div>
                </div>

                {p.photos?.length ? (
                  <div id={`fav-carousel-${p.id}`} className="carousel slide" data-bs-ride="false">
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

                    {p.photos.length > 1 && (
                      <>
                        <button
                          className="carousel-control-prev"
                          type="button"
                          data-bs-target={`#fav-carousel-${p.id}`}
                          data-bs-slide="prev"
                          style={{ filter: "drop-shadow(0 0 6px rgba(255, 255, 255, 0.4))" }}
                          aria-label="Anterior"
                          title="Anterior"
                        >
                          <span className="carousel-control-prev-icon" />
                        </button>
                        <button
                          className="carousel-control-next"
                          type="button"
                          data-bs-target={`#fav-carousel-${p.id}`}
                          data-bs-slide="next"
                          style={{ filter: "drop-shadow(0 0 6px rgba(255, 255, 255, 0.4))" }}
                          aria-label="Siguiente"
                          title="Siguiente"
                        >
                          <span className="carousel-control-next-icon" />
                        </button>
                      </>
                    )}
                  </div>
                ) : (
                  <div className="p-4 text-center text-muted">Sin fotos</div>
                )}

                <div className="card-footer bg-white d-flex justify-content-between align-items-center">
                  <button
                    className={`btn btn-sm ${status === "done"
                      ? "btn-success border-success text-white"
                      : "btn-outline-secondary"
                      }`}
                    onClick={(e) => { e.stopPropagation(); onUpdateStatus(p.id, status === "done" ? "pending" : "done"); }}
                    title={status === "done" ? "Marcar como Pendiente" : "Marcar como Realizado"}
                  >
                    {status === "done" ? "Realizado" : "✓ Marcar realizado"}
                  </button>

                  <button
                    className="btn btn-sm btn-celeste"
                    onClick={(e) => { e.stopPropagation(); openPublicationDetail(p); }}
                  >
                    Ver Detalles
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">
          No tienes publicaciones favoritas aún. ¡Empieza a explorar y agrega tus lugares favoritos! 💝
        </div>
      )}

      {/* Modal de detalles */}
      <PublicationDetailModal
        open={openDetailModal}
        pub={currentPub}
        me={{}}
        token={token}
        onClose={() => setOpenDetailModal(false)}
        onToggleFavorite={() => { }}
      />
    </div>
  );
}

//reemplazamos el ReviewsModal por uno más completo con toda la info de las publicaciones.

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

  const [commentInputs, setCommentInputs] = useState({});
  const isLoggedIn = token; // <-- Para las respuestas a reseñas

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
        const rows = await request(`/api/publications/${pub.id}/reviews`, { token });
        if (!cancel) setList(rows);
      } catch (e) {
        if (!cancel) setErr(e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [open, pub?.id, token]); // Depende de 'open' y 'pub.id'

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
      const rows = await request(`/api/publications/${pub.id}/reviews`, { token });
      setList(rows);
      // Nota: El rating_avg/count de 'pub' (prop) no se actualizará
      // hasta que se cierre y reabra el modal.
    } catch (e) {
      alert(`Error creando reseña: ${e.message}`);
    }
  }
  //FUNCION LIKE REVIEW
  async function handleLikeReview(reviewId) {
    if (!isPremium) {
      alert("Solo los usuarios premium pueden dar me gusta a las reseñas.");
      return;
    }

    // Guardar estado original para rollback
    const originalList = list;

    // Actualización optimista
    setList(prevList => prevList.map(r =>
      r.id === reviewId
        ? {
          ...r,
          is_liked_by_me: !r.is_liked_by_me,
          like_count: r.is_liked_by_me ? r.like_count - 1 : r.like_count + 1
        }
        : r
    ));

    try {
      // Llamada al API
      const data = await request(`/api/publications/reviews/${reviewId}/like`, {
        method: "POST",
        token,
      });

      // Sincronizar con la respuesta del servidor (más segura)
      setList(prevList => prevList.map(r =>
        r.id === reviewId
          ? { ...r, is_liked_by_me: data.is_liked, like_count: data.like_count }
          : r
      ));

    } catch (e) {
      alert('Error al dar me gusta: ' + (e.message || 'Error desconocido'));
      setList(originalList); // Rollback en caso de error
    }
  }

  async function submitComment(e, reviewId) {
    e.preventDefault();
    const commentText = commentInputs[reviewId];

    if (!commentText || !commentText.trim()) {
      return; // No enviar comentarios vacíos
    }
    if (!token) {
      alert("Debes iniciar sesión para comentar.");
      return;
    }

    try {
      // Usamos la nueva ruta del API
      const newComment = await request(`/api/publications/reviews/${reviewId}/comments`, {
        method: "POST",
        token,
        body: { comment: commentText }
      });

      // Actualizar el estado 'list' localmente
      setList(prevList =>
        prevList.map(review =>
          // Encontramos la reseña correcta y añadimos el nuevo comentario a su array
          review.id === reviewId
            ? { ...review, comments: [...(review.comments || []), newComment] }
            // Devolvemos las otras reseñas sin cambios
            : review
        )
      );

      // Limpiar el input para esa reseña específica
      setCommentInputs(prev => ({ ...prev, [reviewId]: "" }));

    } catch (err) {
      alert("Error al publicar el comentario: " + (err?.message || "Error"));
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
                  // --- MODIFICAR EL CONTENIDO DEL 'li' ---
                  <li key={r.id} className="border rounded-3 p-3 mb-2">

                    {/* --- CONTENIDO ORIGINAL DE LA RESEÑA (like, stars, etc.) --- */}
                    <div className="d-flex justify-content-between align-items-center">
                      <div className="d-flex align-items-center gap-3">
                        <Stars value={r.rating} />
                        <button
                          className={`btn btn-sm ${r.is_liked_by_me ? 'btn-danger' : 'btn-outline-danger'} ${!isPremium ? 'disabled' : ''}`}
                          onClick={() => handleLikeReview(r.id)}
                          disabled={!isPremium}
                          title={isPremium ? (r.is_liked_by_me ? "Quitar me gusta" : "Dar me gusta") : "Solo usuarios premium pueden dar me gusta"}
                          style={{ padding: '0.1rem 0.4rem' }}
                        >
                          {r.is_liked_by_me ? '❤️' : '🤍'} {r.like_count}
                        </button>
                      </div>
                      <small className="text-muted">{new Date(r.created_at).toLocaleString()}</small>
                    </div>
                    {r.comment && <div className="mt-1">{r.comment}</div>}
                    <small className="text-muted d-block mt-1">por {r.author_username}</small>
                    {/* --- FIN DEL CONTENIDO ORIGINAL --- */}


                    {/* --- INICIO DEL NUEVO BLOQUE DE COMENTARIOS --- */}
                    <div className="mt-3 ps-3" style={{ borderLeft: '3px solid #eee' }}>

                      {/* Lista de comentarios existentes */}
                      {r.comments && r.comments.length > 0 && (
                        <ul className="list-unstyled mb-2">
                          {r.comments.map(c => (
                            <li key={c.id} className="mb-2">
                              <div className="d-flex justify-content-between align-items-center">
                                <strong className="small">{c.author_username}</strong>
                                <small className="text-muted" style={{ fontSize: '0.75em' }}>
                                  {new Date(c.created_at).toLocaleString()}
                                </small>
                              </div>
                              <p className="mb-0 small" style={{ whiteSpace: 'pre-wrap' }}>{c.comment}</p>
                            </li>
                          ))}
                        </ul>
                      )}

                      {/* Formulario para nuevo comentario (solo si está logueado) */}
                      {isLoggedIn && (
                        <form onSubmit={(e) => submitComment(e, r.id)} className="d-flex gap-2">
                          <input
                            type="text"
                            className="form-control form-control-sm"
                            placeholder="Escribe una respuesta..."
                            value={commentInputs[r.id] || ""}
                            onChange={(e) => setCommentInputs(prev => ({ ...prev, [r.id]: e.target.value }))}
                          />
                          <button
                            className="btn btn-sm btn-celeste"
                            type="submit"
                            // Deshabilitar si el input está vacío
                            disabled={!commentInputs[r.id] || !commentInputs[r.id].trim()}
                          >
                            Enviar
                          </button>
                        </form>
                      )}
                    </div>
                    {/* --- FIN DEL NUEVO BLOQUE DE COMENTARIOS --- */}
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