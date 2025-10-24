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

export default function Backoffice({ me }) {
  const [view, setView] = useState("menu");
  const [loading, setLoading] = useState(false);
  const [pubs, setPubs] = useState([]);
  const [pendingPubs, setPendingPubs] = useState([]);
  const [deletionRequests, setDeletionRequests] = useState([]);
  const [error, setError] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const token = useMemo(() => localStorage.getItem("token") || "", []);

  const fetchedOnce = useRef(false);
  const fetchedPendingOnce = useRef(false);
  const fetchedDeletionOnce = useRef(false);

  // Cargar contador de pendientes al montar el componente
  useEffect(() => {
    (async () => {
      try {
        const data = await request("/api/publications/pending", { token });
        setPendingPubs(data);
        
        const deletionData = await request("/api/publications/deletion-requests/pending", { token });
        setDeletionRequests(deletionData);
      } catch (e) {
        console.error("Error cargando pendientes:", e);
      }
    })();
  }, [token]);

  const go = (v) => {
    setError("");
    setOkMsg("");
    setSearchQuery("");
    setView(v);
  };

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

  useEffect(() => {
    if (view === "list") {
      if (fetchedOnce.current) return;
      fetchedOnce.current = true;
      fetchPublications(searchQuery);
    } else {
      fetchedOnce.current = false;
    }
    
    if (view === "pending") {
      if (fetchedPendingOnce.current) return;
      fetchedPendingOnce.current = true;
      fetchPendingPublications();
    } else {
      fetchedPendingOnce.current = false;
    }
    
    if (view === "deletion-requests") {
      if (fetchedDeletionOnce.current) return;
      fetchedDeletionOnce.current = true;
      fetchDeletionRequests();
    } else {
      fetchedDeletionOnce.current = false;
    }
  }, [view]);

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
      setView("list");
      fetchedOnce.current = false;
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("¿Eliminar esta publicación?")) return;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/${id}`, { method: "DELETE", token });
      setOkMsg("Publicación eliminada.");
      setPubs((prev) => prev.filter((p) => p.id !== id));
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
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleReject(id) {
    if (!window.confirm("¿Rechazar esta publicación? El usuario podrá verla como rechazada.")) return;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/${id}/reject`, { method: "PUT", token });
      setOkMsg("Publicación rechazada.");
      setPendingPubs((prev) => prev.filter((p) => p.id !== id));
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
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRejectDeletion(requestId) {
    if (!window.confirm("¿Rechazar esta solicitud de eliminación?")) return;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/deletion-requests/${requestId}/reject`, { method: "PUT", token });
      setOkMsg("Solicitud de eliminación rechazada.");
      setDeletionRequests((prev) => prev.filter((r) => r.id !== requestId));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      {view === "menu" && <Menu me={me} go={go} pendingCount={pendingPubs.length} deletionCount={deletionRequests.length} />}
      {view === "list" && (
        <ListView
          pubs={pubs}
          loading={loading}
          error={error}
          okMsg={okMsg}
          searchQuery={searchQuery}
          go={go}
          onDelete={handleDelete}
          onSearch={handleSearch}
        />
      )}
      {view === "pending" && (
        <PendingView
          pubs={pendingPubs}
          loading={loading}
          error={error}
          okMsg={okMsg}
          go={go}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
      {view === "deletion-requests" && (
        <DeletionRequestsView
          requests={deletionRequests}
          loading={loading}
          error={error}
          okMsg={okMsg}
          go={go}
          onApprove={handleApproveDeletion}
          onReject={handleRejectDeletion}
        />
      )}
      {view === "create" && (
        <CreateView
          loading={loading}
          error={error}
          okMsg={okMsg}
          go={go}
          onSubmit={handleCreate}
        />
      )}
    </div>
  );
}

/* ------------------- Subcomponentes ------------------- */

function Menu({ me, go, pendingCount, deletionCount }) {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center py-5">
      <h2 className="mb-4">Backoffice</h2>
      <p className="text-muted mb-4">
        Hola {me?.username}. Gestioná las publicaciones.
      </p>
      <div className="d-flex gap-3 flex-wrap justify-content-center">
        <button className="btn btn-primary px-4" onClick={() => go("list")}>
          Listar publicaciones
        </button>
        <button className="btn btn-warning px-4 position-relative" onClick={() => go("pending")}>
          Publicaciones pendientes
          {pendingCount > 0 && (
            <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
              {pendingCount}
            </span>
          )}
        </button>
        <button className="btn btn-danger px-4 position-relative" onClick={() => go("deletion-requests")}>
          Solicitudes de eliminación
          {deletionCount > 0 && (
            <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-dark">
              {deletionCount}
            </span>
          )}
        </button>
        <button
          className="btn btn-outline-primary px-4"
          onClick={() => go("create")}
        >
          Crear publicación
        </button>
      </div>
    </div>
  );
}

function ListView({ pubs, loading, error, okMsg, searchQuery, go, onDelete, onSearch }) {
  function handleSearchSubmit(e) {
    e.preventDefault();
    const searchValue = e.target.search.value.trim();
    onSearch(searchValue);
  }

  return (
    <div className="container py-4">
      <div className="d-flex align-items-center justify-content-between">
        <h3 className="mb-0">Publicaciones</h3>
        <div className="d-flex gap-2">
          <button className="btn btn-outline-secondary" onClick={() => go("menu")}>
            Volver
          </button>
          <button className="btn btn-primary" onClick={() => go("create")}>
            Nueva publicación
          </button>
        </div>
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

function CreateView({ loading, error, okMsg, go, onSubmit }) {
  return (
    <div className="container py-4" style={{ maxWidth: 720 }}>
      <div className="d-flex align-items-center justify-content-between">
        <h3 className="mb-0">Crear publicación</h3>
        <button className="btn btn-outline-secondary" onClick={() => go("menu")}>
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
            onClick={() => go("list")}
          >
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary">
            Crear
          </button>
        </div>
      </form>
    </div>
  );
}

function PendingView({ pubs, loading, error, okMsg, go, onApprove, onReject }) {
  return (
    <div className="container py-4">
      <div className="d-flex align-items-center justify-content-between">
        <h3 className="mb-0">Publicaciones Pendientes de Aprobación</h3>
        <button className="btn btn-outline-secondary" onClick={() => go("menu")}>
          Volver
        </button>
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

function DeletionRequestsView({ requests, loading, error, okMsg, go, onApprove, onReject }) {
  return (
    <div className="container py-4">
      <div className="d-flex align-items-center justify-content-between">
        <h3 className="mb-0">Solicitudes de Eliminación Pendientes</h3>
        <button className="btn btn-outline-secondary" onClick={() => go("menu")}>
          Volver
        </button>
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
                      ✓ Aprobar eliminación
                    </button>
                    <button
                      className="btn btn-secondary btn-sm flex-fill"
                      onClick={() => onReject(req.id)}
                    >
                      ✗ Rechazar solicitud
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
