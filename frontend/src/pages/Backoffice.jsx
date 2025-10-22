import React, { useEffect, useMemo, useState } from "react";

// helper mínimo para requests con token
async function request(path, { method = "GET", token, body, isForm = false } = {}) {
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
  const [error, setError] = useState("");
  const [okMsg, setOkMsg] = useState("");

  const token = useMemo(() => localStorage.getItem("token") || "", []);

  const go = (v) => {
    setError("");
    setOkMsg("");
    setView(v);
  };

  // ---- Listar
  async function fetchPublications() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/publications", { token });
      setPubs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (view === "list") {
      fetchPublications();
    }
  }, [view]);

  // ---- Crear
  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setOkMsg("");
    const form = e.currentTarget;
    const fd = new FormData(form);

    const files = form.photos.files;
    if (files.length > 4) {
      setError("Máximo 4 fotos por publicación.");
      return;
    }

    setLoading(true);
    try {
      const data = await request("/api/publications", { method: "POST", token, body: fd, isForm: true });
      setOkMsg("Publicación creada con éxito.");
      form.reset();
      // redirigir a lista
      setView("list");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // ---- Borrar
  async function handleDelete(id) {
    if (!window.confirm("¿Eliminar esta publicación?")) return;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      await request(`/api/publications/${id}`, { method: "DELETE", token });
      setOkMsg("Publicación eliminada.");
      // refrescar lista
      setPubs((prev) => prev.filter((p) => p.id !== id));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // ---- UI helpers
  function Menu() {
    return (
      <div className="d-flex flex-column align-items-center justify-content-center py-5">
        <h2 className="mb-4">Backoffice</h2>
        <p className="text-muted mb-4">Hola {me?.username}. Gestioná las publicaciones.</p>
        <div className="d-flex gap-3">
          <button className="btn btn-primary px-4" onClick={() => go("list")}>
            Listar publicaciones
          </button>
          <button className="btn btn-outline-primary px-4" onClick={() => go("create")}>
            Crear publicación
          </button>
        </div>
      </div>
    );
  }

  function ListView() {
    useEffect(() => {
      // limpiar alertas al entrar
      setError("");
      setOkMsg("");
      fetchPublications();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
      <div className="container py-4">
        <div className="d-flex align-items-center justify-content-between">
          <h3 className="mb-0">Publicaciones</h3>
          <div className="d-flex gap-2">
            <button className="btn btn-outline-secondary" onClick={() => setView("menu")}>Volver</button>
            <button className="btn btn-primary" onClick={() => setView("create")}>Nueva publicación</button>
          </div>
        </div>

        {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
        {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
        {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

        <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mt-2">
          {pubs.map((p) => (
            <div className="col" key={p.id}>
              <div className="card shadow-sm h-100">
                {/* header con menú */}
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
                          <button className="dropdown-item text-danger" onClick={() => handleDelete(p.id)}>
                            Eliminar publicación
                          </button>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* carrusel de fotos */}
                {p.photos && p.photos.length > 0 ? (
                  <div id={`carousel-${p.id}`} className="carousel slide" data-bs-ride="carousel">
                    <div className="carousel-inner">
                      {p.photos.map((url, idx) => (
                        <div className={`carousel-item ${idx === 0 ? "active" : ""}`} key={url}>
                          <img src={url} className="d-block w-100" alt={`Foto ${idx + 1}`} />
                        </div>
                      ))}
                    </div>
                    {p.photos.length > 1 && (
                      <>
                        <button className="carousel-control-prev" type="button" data-bs-target={`#carousel-${p.id}`} data-bs-slide="prev">
                          <span className="carousel-control-prev-icon" aria-hidden="true"></span>
                          <span className="visually-hidden">Anterior</span>
                        </button>
                        <button className="carousel-control-next" type="button" data-bs-target={`#carousel-${p.id}`} data-bs-slide="next">
                          <span className="carousel-control-next-icon" aria-hidden="true"></span>
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

        {(!loading && pubs.length === 0) && (
          <div className="alert alert-secondary mt-3">No hay publicaciones cargadas aún.</div>
        )}
      </div>
    );
  }

  function CreateView() {
    useEffect(() => {
      // limpiar alertas al entrar
      setError("");
      setOkMsg("");
    }, []);
    
    return (
      <div className="container py-4" style={{ maxWidth: 720 }}>
        <div className="d-flex align-items-center justify-content-between">
          <h3 className="mb-0">Crear publicación</h3>
          <button className="btn btn-outline-secondary" onClick={() => setView("menu")}>Volver</button>
        </div>

        {loading && <div className="alert alert-info mt-3 mb-0">Guardando...</div>}
        {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
        {okMsg && <div className="alert alert-success mt-3 mb-0">{okMsg}</div>}

        <form className="card shadow-sm mt-3 p-3" onSubmit={handleCreate}>
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
              <input name="photos" type="file" className="form-control" multiple accept="image/jpeg,image/png,image/webp" />
              <div className="form-text">Podés seleccionar varias a la vez. Máximo 4.</div>
            </div>
          </div>

          <div className="d-flex justify-content-end gap-2 mt-3">
            <button type="button" className="btn btn-outline-secondary" onClick={() => setView("list")}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary">Crear</button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="container">
      {view === "menu" && <Menu />}
      {view === "list" && <ListView />}
      {view === "create" && <CreateView />}
    </div>
  );
}
