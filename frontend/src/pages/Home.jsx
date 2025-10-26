import React, { useEffect, useMemo, useRef, useState } from "react";

/* Helper fetch */
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
      <button type="button" className="btn btn-outline-primary dropdown-toggle" onClick={() => { setOpen(o => !o); if (!open && onReload) onReload(); }}>
        Categorías
      </button>
      {open && (
        <div ref={boxRef} className="position-absolute end-0 mt-2 p-3 bg-white border rounded-3 shadow" style={{ minWidth: 280, zIndex: 1000, maxHeight: 360, overflow: "auto" }}>
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
            <button className="btn btn-primary" type="button" onClick={apply}>Ver resultados</button>
          </div>
        </div>
      )}
    </div>
  );
}

/* --- Modal reseñas --- */
function ReviewsModal({ open, pub, token, onClose }) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

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
    if (!token) { alert("Iniciá sesión para publicar una reseña."); return; }
    try {
      await request(`/api/publications/${pub.id}/reviews`, {
        method: "POST",
        token,
        body: { rating: Number(rating), comment: comment || undefined }
      });
      setComment("");
      setRating(5);
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

        <form className="p-3 border-top" onSubmit={submitReview}>
          <div className="row g-2">
            <div className="col-12 col-md-2">
              <label className="form-label mb-1">Rating</label>
              <select className="form-select" value={rating} onChange={(e) => setRating(e.target.value)}>
                {[5,4,3,2,1].map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
            <div className="col-12 col-md-8">
              <label className="form-label mb-1">Comentario (opcional)</label>
              <input className="form-control" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Contanos tu experiencia" />
            </div>
            <div className="col-12 col-md-2 d-flex align-items-end">
              <button className="btn btn-primary w-100" type="submit">Publicar</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Home({ me }) {
  const [pubs, setPubs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const token = useMemo(() => localStorage.getItem("token") || "", []);

  const [cats, setCats] = useState([]);            // categorías aplicadas
  const [allCats, setAllCats] = useState([]);      // disponibles (dinámicas)

  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState(null);

  const qs = cats.length ? `?category=${encodeURIComponent(cats.join(","))}` : "";

  async function reloadCats() {
    try {
      const list = await request("/api/categories");
      setAllCats(list);
    } catch (e) {
      // silencio: si no hay endpoint aún, la UI sigue funcionando
    }
  }

  useEffect(() => { reloadCats(); }, []); // cargar al montar

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const data = await request(`/api/publications/public${qs}`);
        setPubs(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [qs]);

  function openReviews(p) { setCurrent(p); setOpen(true); }

  return (
    <div className="container mt-4">
      <div className="p-5 mb-4 bg-light rounded-3">
        <div className="container-fluid py-5">
          <h1 className="display-6 fw-bold">¡Bienvenido a Plan&Go, {me.username}!</h1>
          <p className="col-md-8 fs-5">Usá los filtros para encontrar actividades/lugares y mirá las reseñas antes de decidir.</p>
        </div>
      </div>

      <div className="d-flex align-items-center justify-content-between flex-wrap gap-2">
        <h3 className="mb-0">Publicaciones</h3>
        <MultiCategoryDropdown
          allCats={allCats}
          selected={cats}
          onApply={setCats}
          onReload={reloadCats}
        />
      </div>

      {loading && <div className="alert alert-info mt-3 mb-0">Cargando...</div>}
      {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}

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
                      <RatingBadge avg={p.rating_avg} count={p.rating_count} />
                      {(p.categories || []).map((c) => (
                        <span key={c} className="badge bg-secondary-subtle text-secondary border text-capitalize">{c}</span>
                      ))}
                    </div>
                  </div>
                  <button className="btn btn-sm btn-outline-primary" onClick={() => openReviews(p)}>
                    Ver reseñas
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
                      <button className="carousel-control-prev" type="button" data-bs-target={`#home-carousel-${p.id}`} data-bs-slide="prev" style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }} aria-label="Anterior" title="Anterior">
                        <span className="carousel-control-prev-icon" aria-hidden="true" />
                        <span className="visually-hidden">Anterior</span>
                      </button>
                      <button className="carousel-control-next" type="button" data-bs-target={`#home-carousel-${p.id}`} data-bs-slide="next" style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }} aria-label="Siguiente" title="Siguiente">
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
                <button className="btn btn-link btn-sm" onClick={() => openReviews(p)}>Ver reseñas</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && pubs.length === 0 && (
        <div className="alert alert-secondary mt-3">No hay publicaciones para los filtros seleccionados.</div>
      )}

      <ReviewsModal open={open} pub={current} token={token} onClose={() => setOpen(false)} />
    </div>
  );
}
