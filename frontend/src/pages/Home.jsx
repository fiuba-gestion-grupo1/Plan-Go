import React, { useEffect, useMemo, useState } from "react";
import CreatePublicationForm from "../components/CreatePublicationForm";

async function request(path, { method = "GET", token, body, isForm = false } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isForm) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { method, headers, body: isForm ? body : body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }
  return res.json().catch(() => ({}));
}

export default function Home({ me }) {
  const [pubs, setPubs] = useState([]);
  const [myPubs, setMyPubs] = useState([]);
  const [favPubs, setFavPubs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showMySubmissions, setShowMySubmissions] = useState(false);
  const [showFavorites, setShowFavorites] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const token = useMemo(() => localStorage.getItem("token") || "", []);

  async function fetchPublications(query = "") {
    setLoading(true);
    setError("");
    try {
      const endpoint = query 
        ? `/api/publications/search?q=${encodeURIComponent(query)}`
        : "/api/publications/public";
      const data = await request(endpoint, { token });
      setPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchPublications(searchQuery);
  }, [token]);

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
      
      // Actualizar la lista de publicaciones con el nuevo estado
      setPubs(prevPubs => 
        prevPubs.map(p => 
          p.id === pubId ? { ...p, is_favorite: data.is_favorite } : p
        )
      );
    } catch (e) {
      setError(e.message);
    }
  }

  function handleSearch(query) {
    setSearchQuery(query);
    fetchPublications(query);
  }

  async function handleCreateSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    const form = e.currentTarget;
    const fd = new FormData(form);
    const files = form.photos.files || [];
    if (files.length > 4) {
      setError("Máximo 4 fotos por publicación.");
      return;
    }
    setLoading(true);
    try {
      await request("/api/publications/submit", {
        method: "POST",
        token,
        body: fd,
        isForm: true,
      });
      setSuccessMsg("¡Publicación enviada! Será revisada por un administrador.");
      form.reset();
      setTimeout(() => {
        setShowCreateForm(false);
        setSuccessMsg("");
      }, 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (showCreateForm) {
    return (
      <CreatePublicationForm
        onSubmit={handleCreateSubmit}
        onCancel={() => {
          setShowCreateForm(false);
          setError("");
          setSuccessMsg("");
        }}
        loading={loading}
        error={error}
        successMsg={successMsg}
      />
    );
  }

  if (showMySubmissions) {
    return (
      <MySubmissionsView
        pubs={myPubs}
        loading={loading}
        error={error}
        onBack={() => {
          setShowMySubmissions(false);
          setError("");
        }}
        onLoad={fetchMySubmissions}
      />
    );
  }

  if (showFavorites) {
    return (
      <FavoritesView
        pubs={favPubs}
        loading={loading}
        error={error}
        onBack={() => {
          setShowFavorites(false);
          setError("");
        }}
        onLoad={fetchFavorites}
        onToggleFavorite={async (pubId) => {
          await toggleFavorite(pubId);
          // Recargar favoritos después de quitar uno
          fetchFavorites();
        }}
      />
    );
  }

  function handleSearchSubmit(e) {
    e.preventDefault();
    const searchValue = e.target.search.value.trim();
    handleSearch(searchValue);
  }

  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between">
        <h3 className="mb-0">Publicaciones</h3>
        <div className="d-flex gap-2">
          <button 
            className="btn btn-outline-danger" 
            onClick={() => {
              setShowFavorites(true);
              fetchFavorites();
            }}
          >
            ❤️ Mis Favoritos
          </button>
          <button 
            className="btn btn-outline-secondary" 
            onClick={() => {
              setShowMySubmissions(true);
              fetchMySubmissions();
            }}
          >
            Mis Publicaciones
          </button>
          <button 
            className="btn btn-primary" 
            onClick={() => setShowCreateForm(true)}
          >
            + Agregar Publicación
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
            onClick={() => handleSearch("")}
          >
            Limpiar
          </button>
        </div>
      )}

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className="card shadow-sm h-100">
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted">
                      {p.address}, {p.city}, {p.province}, {p.country}
                    </small>
                  </div>
                  <button
                    className="btn btn-link p-0 ms-2"
                    onClick={() => toggleFavorite(p.id)}
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
                      <button
                        className="carousel-control-prev"
                        type="button"
                        data-bs-target={`#home-carousel-${p.id}`}
                        data-bs-slide="prev"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                        aria-label="Anterior"
                        title="Anterior"
                      >
                        <span className="carousel-control-prev-icon" aria-hidden="true" />
                        <span className="visually-hidden">Anterior</span>
                      </button>

                      <button
                        className="carousel-control-next"
                        type="button"
                        data-bs-target={`#home-carousel-${p.id}`}
                        data-bs-slide="next"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                        aria-label="Siguiente"
                        title="Siguiente"
                      >
                        <span className="carousel-control-next-icon" aria-hidden="true" />
                        <span className="visually-hidden">Siguiente</span>
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center text-muted">Sin fotos</div>
              )}

              <div className="card-footer bg-white">
                <small className="text-muted">Creado: {new Date(p.created_at).toLocaleString()}</small>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">No hay publicaciones disponibles.</div>
      )}
    </div>
  );
}

function MySubmissionsView({ pubs, loading, error, onBack, onLoad }) {
  React.useEffect(() => {
    onLoad();
  }, []);

  const getStatusBadge = (status) => {
    if (status === "approved") return <span className="badge bg-success">Aprobada</span>;
    if (status === "pending") return <span className="badge bg-warning text-dark">Pendiente</span>;
    if (status === "rejected") return <span className="badge bg-danger">Rechazada</span>;
    return <span className="badge bg-secondary">{status}</span>;
  };

  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between mb-4">
        <h3 className="mb-0">Mis Publicaciones</h3>
        <button className="btn btn-outline-secondary" onClick={onBack}>
          Volver
        </button>
      </div>

      {loading && <div className="alert alert-info">Cargando...</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className="card shadow-sm h-100">
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h5 className="card-title mb-1">{p.place_name}</h5>
                  {getStatusBadge(p.status)}
                </div>
                <small className="text-muted">
                  {p.address}, {p.city}, {p.province}, {p.country}
                </small>
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
                <small className="text-muted d-block">
                  Enviado: {new Date(p.created_at).toLocaleString()}
                </small>
                {p.status === "rejected" && (
                  <small className="text-danger d-block mt-1">
                    ❌ Esta publicación fue rechazada por un administrador.
                  </small>
                )}
                {p.status === "pending" && (
                  <small className="text-warning d-block mt-1">
                    ⏳ En revisión por un administrador.
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
    </div>
  );
}

function FavoritesView({ pubs, loading, error, onBack, onLoad, onToggleFavorite }) {
  React.useEffect(() => {
    onLoad();
  }, []);

  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between mb-4">
        <h3 className="mb-0">❤️ Mis Favoritos</h3>
        <button className="btn btn-outline-secondary" onClick={onBack}>
          Volver
        </button>
      </div>

      {loading && <div className="alert alert-info">Cargando...</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className="card shadow-sm h-100 border-danger">
              <div className="card-body pb-0">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    <h5 className="card-title mb-1">{p.place_name}</h5>
                    <small className="text-muted">
                      {p.address}, {p.city}, {p.province}, {p.country}
                    </small>
                  </div>
                  <button
                    className="btn btn-link p-0 ms-2"
                    onClick={() => onToggleFavorite(p.id)}
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
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
                      >
                        <span className="carousel-control-prev-icon" />
                      </button>
                      <button
                        className="carousel-control-next"
                        type="button"
                        data-bs-target={`#fav-carousel-${p.id}`}
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
          No tienes publicaciones favoritas aún. ¡Empieza a explorar y agrega tus lugares favoritos! 💝
        </div>
      )}
    </div>
  );
}
