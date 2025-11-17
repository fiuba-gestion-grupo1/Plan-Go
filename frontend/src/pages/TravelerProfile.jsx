// src/pages/TravelerProfile.jsx
import React, { useEffect, useState } from "react";
import { request } from "../utils/api";
import { RatingBadge } from "../components/shared/UIComponents";

export default function TravelerProfile({ me }) {
  // Nombre “bonito”
  const displayName = me?.first_name || me?.username || "Viajero";
  const username = me?.username || "usuario";
  const location = me?.city || me?.country || "Agregá tu ciudad de origen";
  const bio =
    me?.bio ||
    "Contale a la comunidad qué te gusta cuando viajás: destinos favoritos, estilos de viaje, si preferís low cost, all inclusive, naturaleza, ciudades, etc.";

  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  // Estados para datos reales
  const [publishedItineraries, setPublishedItineraries] = useState([]);
  const [favoritesToVisit, setFavoritesToVisit] = useState([]); // pending
  const [favoritesVisited, setFavoritesVisited] = useState([]); // done

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Cargar itinerarios y favoritos
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        // 1) Itinerarios del usuario
        const its = await request("/api/itineraries/my-itineraries", { token });
        const visibleIts = Array.isArray(its) ? its : [];

        // 2) Favoritos del usuario
        const favs = await request("/api/publications/favorites", { token });
        const favArray = Array.isArray(favs) ? favs : [];

        const toVisit = favArray.filter(
          (p) => (p.favorite_status || "pending") === "pending"
        );
        const visited = favArray.filter(
          (p) => (p.favorite_status || "pending") === "done"
        );

        if (!cancelled) {
          setPublishedItineraries(visibleIts);
          setFavoritesToVisit(toVisit);
          setFavoritesVisited(visited);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message || "Error cargando tu perfil viajero.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const dateOnly = dateStr.split("T")[0];
    const [y, m, d] = dateOnly.split("-");
    const date = new Date(y, m - 1, d);
    return date.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="container-fluid py-4">
      {/* Cabecera */}
      <div className="card border-0 shadow-sm rounded-4 mb-4">
        <div className="card-body d-flex flex-column flex-md-row align-items-md-center">
          {/* Avatar */}
          <div className="traveler-avatar me-md-4 mb-3 mb-md-0 d-flex align-items-center justify-content-center">
            <span className="fw-bold text-white fs-3">
              {displayName.charAt(0).toUpperCase()}
            </span>
          </div>

          {/* Info básica */}
          <div className="flex-grow-1">
            <h1 className="h4 fw-bold mb-1">{displayName}</h1>
            <div className="text-muted small mb-1">@{username}</div>
            <div className="text-muted small mb-2">📍 {location}</div>
            <p className="mb-0 small text-muted">{bio}</p>
          </div>

          {/* CTA futuro: editar perfil */}
          <div className="ms-md-3 mt-3 mt-md-0">
            <button
              type="button"
              className="btn btn-outline-primary btn-sm"
              disabled
            >
              Editar perfil (próximamente)
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="alert alert-info">Cargando tu perfil viajero…</div>
      )}
      {error && <div className="alert alert-danger">{error}</div>}

      {/* Itinerarios publicados (por ahora: todos tus itinerarios) */}
      <div
        className="card shadow-sm rounded-4 mb-4"
        style={{
          background: "rgba(255,255,255,0.60)",
          backdropFilter: "blur(5px)",
          border: "1px solid rgba(255,255,255,0.4)"
        }}
      >
        <div className="card-header bg-light border-0 rounded-top-4">
          <div className="d-flex justify-content-between align-items-center">
            <h2 className="h6 text-uppercase text-muted mb-0">
              Itinerarios publicados
            </h2>
            <small className="text-muted">
              Itinerarios generados que otros viajeros podrían consultar.
            </small>
          </div>
        </div>
        <div className="card-body">
          {!loading && publishedItineraries.length === 0 ? (
            <div className="alert alert-light border mb-0">
              Todavía no tenés itinerarios generados.
              <br />
              Cuando crees itinerarios con IA, más adelante vas a poder elegir
              cuáles mostrar en tu perfil público.
            </div>
          ) : (
            <div className="row g-3">
              {publishedItineraries.map((it) => (
                <div className="col-12 col-md-6 col-lg-4" key={it.id}>
                  <div className="card h-100 border-0 shadow-sm rounded-4">
                    <div className="card-body d-flex flex-column">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <div>
                          <div className="fw-semibold">{it.destination}</div>
                          <div className="small text-muted">
                            {formatDate(it.start_date)} –{" "}
                            {formatDate(it.end_date)}
                          </div>
                        </div>
                        <span className="badge bg-light text-dark border small">
                          {it.trip_type || "Viaje"}
                        </span>
                      </div>

                      <div className="small text-muted mb-2">
                        💰 Presupuesto estimado: US${it.budget} · 👥{" "}
                        {it.cant_persons} persona
                        {it.cant_persons > 1 ? "s" : ""}
                      </div>

                      <div className="mt-auto d-flex justify-content-between align-items-center">
                        <span className="small text-muted">
                          Estado:{" "}
                          {it.status === "completed" && (
                            <span className="badge bg-success">Completado</span>
                          )}
                          {it.status === "pending" && (
                            <span className="badge bg-warning text-dark">
                              Pendiente
                            </span>
                          )}
                          {it.status === "failed" && (
                            <span className="badge bg-danger">Error</span>
                          )}
                        </span>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-primary"
                          disabled
                        >
                          Ver detalle (próx.)
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Favoritos: Por visitar / Visitados */}
      <div className="row g-4">
        {/* Por visitar */}
        <div className="col-12 col-lg-6">
          <div
            className="card shadow-sm rounded-4 h-100"
            style={{
              background: "rgba(255,255,255,0.60)",
              backdropFilter: "blur(5px)",
              border: "1px solid rgba(255,255,255,0.4)"
            }}
          >
            <div className="card-header bg-light border-0 rounded-top-4">
              <h2 className="h6 text-uppercase text-muted mb-0">
                Lugares por visitar
              </h2>
              <small className="text-muted">
                Lugares que marcaste como pendientes de visitar.
              </small>
            </div>
            <div className="card-body">
              {!loading && favoritesToVisit.length === 0 ? (
                <div className="alert alert-light border mb-0 small">
                  Aún no agregaste lugares a <strong>Por visitar</strong>.
                  <br />
                  Desde la sección de favoritos podés marcar los lugares que
                  querés guardar para más adelante.
                </div>
              ) : (
                <div className="row row-cols-1 row-cols-md-2 g-3">
                  {favoritesToVisit.map((p) => (
                    <div className="col" key={p.id}>
                      <div className="card shadow-sm h-100 border-0 rounded-4">
                        <div className="card-body pb-0">
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <h3 className="h6 fw-semibold mb-1">
                                {p.place_name}
                              </h3>
                              <small className="text-muted d-block">
                                📍 {p.address ? `${p.address}, ` : ""}
                                {p.city}, {p.province}
                                {p.country ? `, ${p.country}` : ""}
                              </small>
                              <div className="mt-2 d-flex flex-wrap gap-1">
                                {(p.categories || []).map((c) => (
                                  <span
                                    key={c}
                                    className="badge bg-secondary-subtle text-secondary border text-capitalize"
                                  >
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <div className="text-end ms-2">
                              <span className="badge bg-info-subtle text-info border mb-1">
                                Por visitar
                              </span>
                              <RatingBadge
                                avg={p.rating_avg}
                                count={p.rating_count}
                              />
                            </div>
                          </div>
                        </div>

                        {p.photos?.length ? (
                          <div
                            id={`profile-visit-${p.id}`}
                            className="carousel slide"
                            data-bs-ride="false"
                          >
                            <div className="carousel-inner">
                              {p.photos.map((url, idx) => (
                                <div
                                  className={`carousel-item ${idx === 0 ? "active" : ""
                                    }`}
                                  key={url}
                                >
                                  <img
                                    src={url}
                                    className="d-block w-100"
                                    alt={`Foto ${idx + 1}`}
                                    style={{
                                      height: 200,
                                      objectFit: "cover",
                                    }}
                                  />
                                </div>
                              ))}
                            </div>
                            {p.photos.length > 1 && (
                              <>
                                <button
                                  className="carousel-control-prev"
                                  type="button"
                                  data-bs-target={`#profile-visit-${p.id}`}
                                  data-bs-slide="prev"
                                >
                                  <span
                                    className="carousel-control-prev-icon"
                                    aria-hidden="true"
                                  />
                                  <span className="visually-hidden">
                                    Anterior
                                  </span>
                                </button>
                                <button
                                  className="carousel-control-next"
                                  type="button"
                                  data-bs-target={`#profile-visit-${p.id}`}
                                  data-bs-slide="next"
                                >
                                  <span
                                    className="carousel-control-next-icon"
                                    aria-hidden="true"
                                  />
                                  <span className="visually-hidden">
                                    Siguiente
                                  </span>
                                </button>
                              </>
                            )}
                          </div>
                        ) : (
                          <div className="p-3 text-center text-muted">
                            Sin fotos
                          </div>
                        )}

                        <div className="card-footer bg-white border-0 d-flex justify-content-between align-items-center">
                          <small className="text-muted">
                            Desde{" "}
                            <span className="text-success fw-semibold">
                              US${p.cost_per_day}
                            </span>
                          </small>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Visitados */}
        <div className="col-12 col-lg-6">
          <div
            className="card shadow-sm rounded-4 h-100"
            style={{
              background: "rgba(255,255,255,0.60)",
              backdropFilter: "blur(5px)",
              border: "1px solid rgba(255,255,255,0.4)"
            }}
          >
            <div className="card-header bg-light border-0 rounded-top-4">
              <h2 className="h6 text-uppercase text-muted mb-0">
                Lugares visitados
              </h2>
              <small className="text-muted">
                Lugares que ya visitaste y recomendás a otros viajeros.
              </small>
            </div>
            <div className="card-body">
              {!loading && favoritesVisited.length === 0 ? (
                <div className="alert alert-light border mb-0 small">
                  Aún no agregaste lugares a <strong>Visitados</strong>.
                  <br />
                  Cuando marques favoritos como realizados, van a aparecer acá.
                </div>
              ) : (
                <div className="row row-cols-1 row-cols-md-2 g-3">
                  {favoritesVisited.map((p) => (
                    <div className="col" key={p.id}>
                      <div className="card shadow-sm h-100 border-0 rounded-4">
                        <div className="card-body pb-0">
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <h3 className="h6 fw-semibold mb-1">
                                {p.place_name}
                              </h3>
                              <small className="text-muted d-block">
                                📍 {p.address ? `${p.address}, ` : ""}
                                {p.city}, {p.province}
                                {p.country ? `, ${p.country}` : ""}
                              </small>
                              <div className="mt-2 d-flex flex-wrap gap-1">
                                {(p.categories || []).map((c) => (
                                  <span
                                    key={c}
                                    className="badge bg-secondary-subtle text-secondary border text-capitalize"
                                  >
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <div className="text-end ms-2">
                              <span className="badge bg-success-subtle text-success border mb-1">
                                Visitado
                              </span>
                              <RatingBadge
                                avg={p.rating_avg}
                                count={p.rating_count}
                              />
                            </div>
                          </div>
                        </div>

                        {p.photos?.length ? (
                          <div
                            id={`profile-done-${p.id}`}
                            className="carousel slide"
                            data-bs-ride="false"
                          >
                            <div className="carousel-inner">
                              {p.photos.map((url, idx) => (
                                <div
                                  className={`carousel-item ${idx === 0 ? "active" : ""
                                    }`}
                                  key={url}
                                >
                                  <img
                                    src={url}
                                    className="d-block w-100"
                                    alt={`Foto ${idx + 1}`}
                                    style={{
                                      height: 200,
                                      objectFit: "cover",
                                    }}
                                  />
                                </div>
                              ))}
                            </div>
                            {p.photos.length > 1 && (
                              <>
                                <button
                                  className="carousel-control-prev"
                                  type="button"
                                  data-bs-target={`#profile-done-${p.id}`}
                                  data-bs-slide="prev"
                                >
                                  <span
                                    className="carousel-control-prev-icon"
                                    aria-hidden="true"
                                  />
                                  <span className="visually-hidden">
                                    Anterior
                                  </span>
                                </button>
                                <button
                                  className="carousel-control-next"
                                  type="button"
                                  data-bs-target={`#profile-done-${p.id}`}
                                  data-bs-slide="next"
                                >
                                  <span
                                    className="carousel-control-next-icon"
                                    aria-hidden="true"
                                  />
                                  <span className="visually-hidden">
                                    Siguiente
                                  </span>
                                </button>
                              </>
                            )}
                          </div>
                        ) : (
                          <div className="p-3 text-center text-muted">
                            Sin fotos
                          </div>
                        )}

                        <div className="card-footer bg-white border-0 d-flex justify-content-between align-items-center">
                          <small className="text-muted">
                            Desde{" "}
                            <span className="text-success fw-semibold">
                              US${p.cost_per_day}
                            </span>
                          </small>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
