import React, { useEffect, useMemo, useRef, useState } from "react";

async function request(
  path,
  { method = "GET", token, body, isForm = false } = {}
) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isForm) headers["Content-Type"] = "application/json";

  const res = await fetch(path, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
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

export default function Backoffice({ me, view = "publications" }) {
  const [subView, setSubView] = useState(null); // Para navegación interna
  const [loading, setLoading] = useState(false);
  const [pubs, setPubs] = useState([]);
  const [allPubs, setAllPubs] = useState([]);
  const [pendingPubs, setPendingPubs] = useState([]);
  const [deletionRequests, setDeletionRequests] = useState([]);
  const [error, setError] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const token = useMemo(() => localStorage.getItem("token") || "", []);
  const fetchedOnce = useRef(false);

  // Función para recargar estadísticas
  async function reloadStats() {
    try {
      const [pending, deletions] = await Promise.all([
        request("/api/publications/pending", { token }).catch(() => []),
        request("/api/publications/deletion-requests/pending", { token }).catch(() => [])
      ]);
      setPendingPubs(pending);
      setDeletionRequests(deletions);
    } catch (e) {
      console.error("Error recargando estadísticas:", e);
    }
  }

  async function fetchPublications(query = "") {
    setLoading(true);
    setError("");
    try {
      const endpoint = query 
        ? `/api/publications/search?q=${encodeURIComponent(query)}`
        : "/api/publications";
      const data = await request(endpoint, { token });
      setPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchPendingPublications() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/publications/pending", { token });
      setPendingPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchDeletionRequests() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/publications/deletion-requests/pending", { token });
      setDeletionRequests(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchAllPublications() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/publications/all", { token });
      setAllPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Cargar estadísticas al inicio (siempre)
  useEffect(() => {
    if (!token) return;
    reloadStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // Cargar datos según la vista activa
  useEffect(() => {
    if (view === "publications" && !subView) {
      fetchPublications(searchQuery);
    } else if (view === "all-publications" && !subView) {
      fetchAllPublications();
    } else if (view === "pending" && !subView) {
      fetchPendingPublications();
    } else if (view === "deletion-requests" && !subView) {
      fetchDeletionRequests();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, token]);

  function handleSearch(query) {
    setSearchQuery(query);
    fetchedOnce.current = false;
    fetchPublications(query);
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setOkMsg("");
    const form = e.currentTarget;
    const fd = new FormData(form);
    const files = form.photos.files || [];
    if (files.length > 4) {
      setError("Máximo 4 fotos por publicación.");
      return;
    }
    setLoading(true);
    try {
      await request("/api/publications", {
        method: "POST",
        token,
        body: fd,
        isForm: true,
      });
      setOkMsg("Publicación creada con éxito.");
      form.reset();
      setSubView(null);
      fetchPublications(searchQuery);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id) {
    const reason = window.prompt("¿Por qué eliminas esta publicación? (El usuario verá este mensaje)");
    if (reason === null) return; // Usuario canceló
    
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/${id}`, { 
        method: "DELETE", 
        token,
        body: { reason: reason.trim() || undefined }
      });
      setOkMsg("Publicación marcada como eliminada.");
      setPubs((prev) => prev.filter((p) => p.id !== id));
      setAllPubs((prev) => prev.map((p) => 
        p.id === id ? { ...p, status: 'deleted', rejection_reason: reason.trim() } : p
      ));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(id) {
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/${id}/approve`, { method: "PUT", token });
      setOkMsg("Publicación aprobada.");
      setPendingPubs((prev) => prev.filter((p) => p.id !== id));
      // Recargar estadísticas después de aprobar
      await reloadStats();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleReject(id) {
    const reason = window.prompt("¿Por qué rechazas esta publicación? (El usuario verá este mensaje)");
    if (reason === null) return; // Usuario canceló
    
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/${id}/reject`, { 
        method: "PUT", 
        token,
        body: { reason: reason.trim() || undefined }
      });
      setOkMsg("Publicación rechazada.");
      setPendingPubs((prev) => prev.filter((p) => p.id !== id));
      // Recargar estadísticas después de rechazar
      await reloadStats();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleApproveDeletion(requestId) {
    if (!window.confirm("¿Aprobar esta solicitud de eliminación? La publicación será eliminada permanentemente.")) return;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/deletion-requests/${requestId}/approve`, { method: "PUT", token });
      setOkMsg("Solicitud aprobada. Publicación eliminada.");
      setDeletionRequests((prev) => prev.filter((r) => r.id !== requestId));
      // Recargar estadísticas después de aprobar eliminación
      await reloadStats();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRejectDeletion(requestId) {
    const reason = window.prompt("¿Por qué rechazas esta solicitud de eliminación? (El usuario verá este mensaje)");
    if (reason === null) return; // Usuario canceló
    
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/deletion-requests/${requestId}/reject`, { 
        method: "PUT", 
        token,
        body: { reason: reason.trim() || undefined }
      });
      setOkMsg("Solicitud de eliminación rechazada.");
      setDeletionRequests((prev) => prev.filter((r) => r.id !== requestId));
      // Recargar estadísticas después de rechazar eliminación
      await reloadStats();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Mostrar formulario de crear publicación
  if (subView === 'create') {
    return (
      <CreateView
        loading={loading}
        error={error}
        okMsg={okMsg}
        onBack={() => setSubView(null)}
        onSubmit={handleCreate}
      />
    );
  }

  // Layout con sidebar de estadísticas
  const renderViewWithStats = (content) => (
    <div className="container-fluid py-4">
      <div className="row">
        <div className="col-lg-9">
          {content}
        </div>
        <div className="col-lg-3">
          <StatsSidebar
            totalPubs={view === "all-publications" ? allPubs.filter(p => p.status === "approved").length : pubs.length}
            pendingPubs={pendingPubs.length}
            deletionRequests={deletionRequests.length}
          />
        </div>
      </div>
    </div>
  );

  // Vista de publicaciones aprobadas
  if (view === "publications") {
    return renderViewWithStats(
      <ListView
        pubs={pubs}
        loading={loading}
        error={error}
        okMsg={okMsg}
        searchQuery={searchQuery}
        onDelete={handleDelete}
        onSearch={handleSearch}
        onCreate={() => setSubView('create')}
      />
    );
  }

  // Vista de TODAS las publicaciones (aprobadas, rechazadas, pendientes, eliminadas)
  if (view === "all-publications") {
    return renderViewWithStats(
      <AllPublicationsView
        pubs={allPubs}
        loading={loading}
        error={error}
        okMsg={okMsg}
        onDelete={handleDelete}
      />
    );
  }

  // Vista de aprobación de publicaciones pendientes
  if (view === "pending") {
    return renderViewWithStats(
      <PendingView
        pubs={pendingPubs}
        loading={loading}
        error={error}
        okMsg={okMsg}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    );
  }

  // Vista de solicitudes de eliminación
  if (view === "deletion-requests") {
    return renderViewWithStats(
      <DeletionRequestsView
        requests={deletionRequests}
        loading={loading}
        error={error}
        okMsg={okMsg}
        onApprove={handleApproveDeletion}
        onReject={handleRejectDeletion}
      />
    );
  }

  return null;
}

// Componente de estadísticas en el sidebar
function StatsSidebar({ totalPubs, pendingPubs, deletionRequests }) {
  return (
    <div className="position-sticky" style={{ top: 20 }}>
      <div className="card shadow-sm">
        <div className="card-header">
          <h5 className="mb-0">Estadísticas</h5>
        </div>
        <div className="card-body">
          <div className="mb-3 pb-3 border-bottom">
            <div className="d-flex justify-content-between align-items-center">
              <span className="text-muted">Publicaciones</span>
              <span className="badge text-dark fs-6">{totalPubs}</span>
            </div>
          </div>
          
          <div className="mb-3 pb-3 border-bottom">
            <div className="d-flex justify-content-between align-items-center">
              <span className="text-muted"> Aprobaciones pendientes</span>
              <span className="badge text-dark fs-6">{pendingPubs}</span>
            </div>
          </div>
          
          <div>
            <div className="d-flex justify-content-between align-items-center">
              <span className="text-muted"> Eliminaciones pendientes</span>
              <span className="badge text-dark fs-6">{deletionRequests}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ListView({ pubs, loading, error, okMsg, searchQuery, onDelete, onSearch, onCreate }) {
  function handleSearchSubmit(e) {
    e.preventDefault();
    const searchValue = e.target.search.value.trim();
    onSearch(searchValue);
  }

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Gestión de Publicaciones</h3>
        <button className="btn"  style={{ borderColor: '#3A92B5', color: '#3A92B5' }} onClick={onCreate}>
          + Agregar Publicación
        </button>
      </div>

      {/* Campo de búsqueda */}
      <form className="d-flex mt-3" onSubmit={handleSearchSubmit}>
        <input
          className="form-control"
          type="search"
          name="search"
          defaultValue={searchQuery}
          placeholder="Buscar por país, ciudad, lugar..."
          aria-label="Buscar"
        />
      </form>

      {searchQuery && (
        <div className="alert alert-info d-flex justify-content-between align-items-center mt-3" role="alert">
          <span>
            <strong>Búsqueda:</strong> "{searchQuery}" - {pubs.length} resultado{pubs.length !== 1 ? 's' : ''} encontrado{pubs.length !== 1 ? 's' : ''}
          </span>
          <button 
            className="btn btn-sm btn-outline-secondary" 
            onClick={() => onSearch("")}
          >
            Limpiar
          </button>
        </div>
      )}

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
      {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className="card shadow-sm h-100">
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted">
                      {p.address}, {p.city}, {p.province}, {p.country}
                    </small>
                    <div className="mt-2 d-flex flex-wrap gap-2">
                      <span className="badge bg-light text-dark border">
                        <Stars value={p.rating_avg || 0} />{" "}
                        <span className="ms-1">
                          {Number(p.rating_avg || 0).toFixed(1)} • {p.rating_count || 0} reseña{(p.rating_count||0)===1?"":"s"}
                        </span>
                      </span>
                      {(p.categories || []).map((c) => (
                        <span key={c} className="badge bg-secondary-subtle text-secondary border">{c}</span>
                      ))}
                    </div>
                  </div>
                  <div className="dropdown">
                    <button
                      className="btn btn-sm btn-link text-muted"
                      data-bs-toggle="dropdown"
                      aria-expanded="false"
                      title="Más acciones"
                    >
                      ⋯
                    </button>
                    <ul className="dropdown-menu dropdown-menu-end">
                      <li>
                        <button
                          className="dropdown-item text-danger"
                          onClick={() => onDelete(p.id)}
                        >
                          Eliminar publicación
                        </button>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {p.photos?.length ? (
                <div
                  id={`carousel-${p.id}`}
                  className="carousel slide"
                  data-bs-ride="false"
                >
                  <div className="carousel-inner">
                    {p.photos.map((url, idx) => (
                      <div
                        className={`carousel-item ${idx === 0 ? "active" : ""}`}
                        key={url}
                      >
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
                        data-bs-target={`#carousel-${p.id}`}
                        data-bs-slide="prev"
                        style={{
                          filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))",
                        }}
                        aria-label="Anterior"
                        title="Anterior"
                      >
                        <span
                          className="carousel-control-prev-icon"
                          aria-hidden="true"
                        />
                        <span className="visually-hidden">Anterior</span>
                      </button>

                      <button
                        className="carousel-control-next"
                        type="button"
                        data-bs-target={`#carousel-${p.id}`}
                        data-bs-slide="next"
                        style={{
                          filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))",
                        }}
                        aria-label="Siguiente"
                        title="Siguiente"
                      >
                        <span
                          className="carousel-control-next-icon"
                          aria-hidden="true"
                        />
                        <span className="visually-hidden">Siguiente</span>
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center text-muted">Sin fotos</div>
              )}

              <div className="card-footer bg-white">
                <small className="text-muted">
                  Creado: {new Date(p.created_at).toLocaleString()}
                </small>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">
          No hay publicaciones cargadas aún.
        </div>
      )}
    </div>
  );
}

function CreateView({ loading, error, okMsg, onBack, onSubmit }) {
  return (
    <div className="container py-4" style={{ maxWidth: 720 }}>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Crear publicación</h3>
        <button className="btn btn-outline-secondary" onClick={onBack}>
          Volver
        </button>
      </div>

      {loading && <div className="alert alert-info mt-3 mb-0">Guardando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
      {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

      <form className="card shadow-sm mt-3 p-3" onSubmit={onSubmit}>
        <div className="row g-3">
          <div className="col-12">
            <label className="form-label">Nombre del lugar *</label>
            <input name="place_name" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">País *</label>
            <input name="country" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Provincia/Estado *</label>
            <input name="province" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Ciudad *</label>
            <input name="city" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Dirección (calle y número) *</label>
            <input name="address" type="text" className="form-control" required />
          </div>

          <div className="col-12">
            <label className="form-label">Categorías (CSV) *</label>
            <input name="categories" type="text" className="form-control" placeholder="ej: aventura,cultura" required />
            <div className="form-text">Usá slugs: aventura, cultura, gastronomia</div>
          </div>
        
                  {/* Informacion para relacionar con preferencias*/}
          <hr className="my-3" />
          <div className="col-12">
            <h6 className="text-muted mb-0">Informacion del destino</h6>
            <small className="text-muted">
              Estos campos ayudan al sistema a recomendar destinos según las preferencias de los usuarios.
            </small>
          </div>

          <div className="col-md-6">
            <label className="form-label">Continente</label>
            <select className="form-select" name="continent" defaultValue="">
              <option value="">—</option>
              <option value="américa">América</option>
              <option value="europa">Europa</option>
              <option value="asia">Asia</option>
              <option value="áfrica">África</option>
              <option value="oceanía">Oceanía</option>
            </select>
          </div>

          <div className="col-md-6">
            <label className="form-label">Clima</label>
            <select className="form-select" name="climate" defaultValue="">
              <option value="">—</option>
              <option value="templado">Templado</option>
              <option value="tropical">Tropical</option>
              <option value="frio">Frío</option>
              <option value="seco">Seco</option>
            </select>
          </div>

          <div className="col-12">
            <label className="form-label">Actividades</label>
            <input
              name="activities"
              type="text"
              className="form-control"
              placeholder="ej: playa,gastronomía,noche"
            />
            <div className="form-text">Separá por comas. Se guardan en minúsculas.</div>
          </div>

          <div className="col-md-6">
            <label className="form-label">Costo por día (USD)</label>
            <input
              name="cost_per_day"
              type="number"
              className="form-control"
              min="0"
              step="0.01"
            />
          </div>

          <div className="col-md-6">
            <label className="form-label">Duración (días)</label>
            <input
              name="duration_days"
              type="number"
              className="form-control"
              min="1"
            />
          </div>

          <div className="col-12">
            <label className="form-label">Fotos (hasta 4) — JPG/PNG/WebP</label>
            <input
              name="photos"
              type="file"
              className="form-control"
              multiple
              accept="image/jpeg,image/png,image/webp"
            />
            <div className="form-text">
              Podés seleccionar varias a la vez. Máximo 4.
            </div>
          </div>
        </div>

        <div className="d-flex justify-content-end gap-2 mt-3">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={onBack}
          >
            Cancelar
          </button>
          <button type="submit" className="btn " disabled={loading}>
            {loading ? 'Creando...' : 'Crear'}
          </button>
        </div>
      </form>
    </div>
  );
}

function PendingView({ pubs, loading, error, okMsg, onApprove, onReject }) {
  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Publicaciones Pendientes de Aprobación</h3>
      </div>

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
      {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className="card shadow-sm h-100 border-warning">
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted">
                      {p.address}, {p.city}, {p.province}, {p.country}
                    </small>
                  </div>
                  <span className="badge bg-warning text-dark">Pendiente</span>
                </div>
              </div>

              {p.photos?.length ? (
                <div
                  id={`pending-carousel-${p.id}`}
                  className="carousel slide"
                  data-bs-ride="false"
                >
                  <div className="carousel-inner">
                    {p.photos.map((url, idx) => (
                      <div
                        className={`carousel-item ${idx === 0 ? "active" : ""}`}
                        key={url}
                      >
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
                        data-bs-target={`#pending-carousel-${p.id}`}
                        data-bs-slide="prev"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                      >
                        <span className="carousel-control-prev-icon" />
                      </button>
                      <button
                        className="carousel-control-next"
                        type="button"
                        data-bs-target={`#pending-carousel-${p.id}`}
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
                <small className="text-muted d-block mb-2">
                  Enviado: {new Date(p.created_at).toLocaleString()}
                </small>
                <div className="d-flex gap-2">
                  <button
                    className="btn btn-success btn-sm flex-fill"
                    onClick={() => onApprove(p.id)}
                  >
                    ✓ Aprobar
                  </button>
                  <button
                    className="btn btn-danger btn-sm flex-fill"
                    onClick={() => onReject(p.id)}
                  >
                    ✗ Rechazar
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">
          No hay publicaciones pendientes de aprobación.
        </div>
      )}
    </div>
  );
}

function DeletionRequestsView({ requests, loading, error, okMsg, onApprove, onReject }) {
  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Solicitudes de Eliminación Pendientes</h3>
      </div>

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
      {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {requests.map((req) => {
          const p = req.publication;
          return (
            <div className="col" key={req.id}>
              <div className="card shadow-sm h-100 border-danger">
                <div className="card-body pb-0">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h5 className="card-title mb-1">{p.place_name}</h5>
                      <small className="text-muted">
                        {p.address}, {p.city}, {p.province}, {p.country}
                      </small>
                    </div>
                    <span className="badge bg-danger">Eliminación solicitada</span>
                  </div>
                </div>

                {p.photos?.length ? (
                  <div
                    id={`deletion-carousel-${p.id}`}
                    className="carousel slide"
                    data-bs-ride="false"
                  >
                    <div className="carousel-inner">
                      {p.photos.map((url, idx) => (
                        <div
                          className={`carousel-item ${idx === 0 ? "active" : ""}`}
                          key={url}
                        >
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
                          data-bs-target={`#deletion-carousel-${p.id}`}
                          data-bs-slide="prev"
                          style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                        >
                          <span className="carousel-control-prev-icon" />
                        </button>
                        <button
                          className="carousel-control-next"
                          type="button"
                          data-bs-target={`#deletion-carousel-${p.id}`}
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
                  <small className="text-muted d-block mb-2">
                    Solicitado: {new Date(req.created_at).toLocaleString()}
                  </small>
                  <div className="d-flex gap-2">
                    <button
                      className="btn btn-success btn-sm flex-fill"
                      onClick={() => onApprove(req.id)}
                    >
                      ✓ Aprobar 
                    </button>
                    <button
                      className="btn btn-secondary btn-sm flex-fill"
                      onClick={() => onReject(req.id)}
                    >
                      ✗ Rechazar 
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!loading && requests.length === 0 && (
        <div className="alert alert-secondary mt-3">
          No hay solicitudes de eliminación pendientes.
        </div>
      )}
    </div>
  );
}

function AllPublicationsView({ pubs, loading, error, okMsg, onDelete }) {
  const getStatusBadge = (status) => {
    if (status === "approved") return <span className="badge bg-success">✓ Aprobada</span>;
    if (status === "pending") return <span className="badge bg-warning text-dark">⏳ Pendiente</span>;
    if (status === "rejected") return <span className="badge bg-danger">✗ Rechazada</span>;
    if (status === "deleted") return <span className="badge bg-dark">🗑️ Eliminada</span>;
    return <span className="badge bg-secondary">{status}</span>;
  };

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Todas las Publicaciones</h3>
      </div>

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
      {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className={`card shadow-sm h-100 ${p.status === 'deleted' ? 'border-dark' : ''}`}>
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <div className="flex-grow-1">
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted d-block">
                      {p.address}, {p.city}, {p.province}, {p.country}
                    </small>
                  </div>
                  <div className="d-flex flex-column align-items-end gap-2">
                    {getStatusBadge(p.status)}
                    {p.status === "approved" && (
                      <div className="dropdown">
                        <button
                          className="btn btn-sm btn-link text-muted p-0"
                          data-bs-toggle="dropdown"
                          aria-expanded="false"
                          title="Más acciones"
                        >
                          ⋯
                        </button>
                        <ul className="dropdown-menu dropdown-menu-end">
                          <li>
                            <button
                              className="dropdown-item text-danger"
                              onClick={() => onDelete(p.id)}
                            >
                              Eliminar publicación
                            </button>
                          </li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {p.photos?.length ? (
                <div id={`all-carousel-${p.id}`} className="carousel slide" data-bs-ride="false">
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
                        data-bs-target={`#all-carousel-${p.id}`}
                        data-bs-slide="prev"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                      >
                        <span className="carousel-control-prev-icon" />
                      </button>
                      <button
                        className="carousel-control-next"
                        type="button"
                        data-bs-target={`#all-carousel-${p.id}`}
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
                <small className="text-muted d-block">
                  Creado: {new Date(p.created_at).toLocaleString()}
                </small>
                {(p.status === "rejected" || p.status === "deleted") && p.rejection_reason && (
                  <small className={`d-block mt-1 ${p.status === "deleted" ? "text-dark" : "text-danger"}`}>
                    {p.status === "deleted" ? "🗑️" : "❌"} <strong>Motivo:</strong> {p.rejection_reason}
                  </small>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">
          No hay publicaciones.
        </div>
      )}
    </div>
  );
}
