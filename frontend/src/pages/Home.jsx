import React, { useEffect, useMemo, useState } from "react";

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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const token = useMemo(() => localStorage.getItem("token") || "", []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const data = await request("/api/publications/public", { token });
        setPubs(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  return (
    <div className="container mt-4">
      <div className="p-5 mb-4 bg-light rounded-3">
        <div className="container-fluid py-5">
          <h1 className="display-5 fw-bold">¡Bienvenido a Plan&Go, {me.username}!</h1>
          <p className="col-md-8 fs-4">
            Empieza a planificar nuevas aventuras! Utiliza el menú de navegación para explorar tu perfil.
          </p>
        </div>
      </div>

      <div className="d-flex align-items-center justify-content-between">
        <h3 className="mb-0">Publicaciones</h3>
      </div>

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}

      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
        {pubs.map((p) => (
          <div className="col" key={p.id}>
            <div className="card shadow-sm h-100">
              <div className="card-body pb-0">
                <h5 className="card-title mb-1">{p.place_name}</h5>
                <small className="text-muted">
                  {p.address}, {p.city}, {p.province}, {p.country}
                </small>
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
