// src/pages/TravelerProfile.jsx
import React, { useEffect, useState } from "react";
import { request } from "../utils/api";
import { RatingBadge } from "../components/shared/UIComponents";
// ⭐ Importamos el mismo modal de detalles que usás en Home.jsx
import PublicationDetailModal from "../components/PublicationDetailModal";

export default function TravelerProfile({ me }) {
  // Nombre “bonito”
  const displayName = me?.first_name || me?.username || "Viajero";
  const username = me?.username || "usuario";
  const bio =
    me?.bio ||
    "Contale a la comunidad qué te gusta cuando viajás: destinos favoritos, estilos de viaje, si preferís low cost, all inclusive, naturaleza, ciudades, etc.";

  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .join("")
    .slice(0, 1)
    .toUpperCase();

  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  // Estados para datos reales
  const [publishedItineraries, setPublishedItineraries] = useState([]);
  const [favoritesToVisit, setFavoritesToVisit] = useState([]); // pending
  const [favoritesVisited, setFavoritesVisited] = useState([]); // done

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ⭐ Estado para el modal de detalle de publicación
  const [openDetailModal, setOpenDetailModal] = useState(false);
  const [currentPub, setCurrentPub] = useState(null);

  const [selectedItineraryDetail, setSelectedItineraryDetail] = useState(null);
  const [openItineraryDetail, setOpenItineraryDetail] = useState(false);

  // ⭐ Función para abrir el detalle
  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

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
          <div
            className="d-flex align-items-center justify-content-center me-md-4 mb-3 mb-md-0"
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              overflow: "hidden",
              flexShrink: 0,
              // CAMBIO: Fondo gris/azul (#6c757d) si no hay foto
              backgroundColor: me?.profile_picture_url ? "transparent" : "#6c757d",
              color: me?.profile_picture_url ? "inherit" : "#FFFFFF", // Letras blancas
            }}
          >
            {me?.profile_picture_url ? (
              <img
                src={me.profile_picture_url}
                alt={displayName}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  borderRadius: "50%",
                }}
              />
            ) : (
              // Contenedor de iniciales centrado
              <span className="fw-bold" style={{ fontSize: "1.4rem" }}>
                {initials}
              </span>
            )}
          </div>

          {/* Info básica */}
          <div className="flex-grow-1">
            <h1 className="h4 fw-bold mb-1">{displayName}</h1>
            <div className="text-muted small mb-1">@{username}</div>
            <p className="mb-0 small text-muted">{bio}</p>
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
          border: "1px solid rgba(255,255,255,0.4)",
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
                          onClick={() => {
                            setSelectedItineraryDetail(it);
                            setOpenItineraryDetail(true);
                          }}
                        >
                          Ver detalle
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
              border: "1px solid rgba(255,255,255,0.4)",
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
                      {/* ⭐ Card clickeable para abrir el detalle */}
                      <div
                        className="card shadow-sm h-100 border-0 rounded-4"
                        style={{ cursor: "pointer" }}
                        onClick={() => openPublicationDetail(p)}
                      >
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
                            className="carousel slide mt-2" // ⭐ espacio entre texto y fotos
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
                                  onClick={(e) => e.stopPropagation()} // ⭐ no romper el click de la card
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
                                  onClick={(e) => e.stopPropagation()}
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
              border: "1px solid rgba(255,255,255,0.4)",
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
                      {/* ⭐ Card clickeable también */}
                      <div
                        className="card shadow-sm h-100 border-0 rounded-4"
                        style={{ cursor: "pointer" }}
                        onClick={() => openPublicationDetail(p)}
                      >
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
                            className="carousel slide mt-2" // ⭐ espacio extra
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
                                  onClick={(e) => e.stopPropagation()}
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
                                  onClick={(e) => e.stopPropagation()}
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

      {/* Modal de detalle de itinerario */}
      {openItineraryDetail && selectedItineraryDetail && (
        <div
          className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{ background: "rgba(0,0,0,.4)", zIndex: 1050 }}
        >
          <div
            className="bg-white rounded-3 shadow-lg border w-100"
            style={{ maxWidth: 900, maxHeight: "90vh", overflow: "auto" }}
          >
            {/* Header */}
            <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                Itinerario: {selectedItineraryDetail.destination}
              </h5>
              <button
                className="btn btn-sm btn-outline-secondary"
                onClick={() => {
                  setOpenItineraryDetail(false);
                  setSelectedItineraryDetail(null);
                }}
              >
                Cerrar
              </button>
            </div>

            {/* Info básica del itinerario */}
            <div className="p-3">
              <div className="card shadow-sm mb-4">
                <div className="card-body">
                  <div className="row mb-3">
                    <div className="col-md-6">
                      <p>
                        <strong>📅 Fechas:</strong>{" "}
                        {formatDate(selectedItineraryDetail.start_date)} –{" "}
                        {formatDate(selectedItineraryDetail.end_date)}
                      </p>
                      <p>
                        <strong>🎯 Tipo de viaje:</strong>{" "}
                        {selectedItineraryDetail.trip_type}
                      </p>
                      <p>
                        <strong>💰 Presupuesto:</strong>{" "}
                        US${selectedItineraryDetail.budget}
                      </p>
                      <p>
                        <strong>👥 Personas:</strong>{" "}
                        {selectedItineraryDetail.cant_persons}
                      </p>
                    </div>
                    <div className="col-md-6">
                      {selectedItineraryDetail.arrival_time && (
                        <p>
                          <strong>🛬 Hora de llegada:</strong>{" "}
                          {selectedItineraryDetail.arrival_time}
                        </p>
                      )}
                      {selectedItineraryDetail.departure_time && (
                        <p>
                          <strong>🛫 Hora de salida:</strong>{" "}
                          {selectedItineraryDetail.departure_time}
                        </p>
                      )}
                      <p>
                        <strong>Estado:</strong>{" "}
                        {selectedItineraryDetail.status === "completed" && (
                          <span className="badge bg-success">Completado</span>
                        )}
                        {selectedItineraryDetail.status === "pending" && (
                          <span className="badge bg-warning text-dark">
                            Pendiente
                          </span>
                        )}
                        {selectedItineraryDetail.status === "failed" && (
                          <span className="badge bg-danger">Error</span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Itinerario generado por IA */}
              <div className="card shadow-sm mb-4">
                <div className="card-header bg-info text-white d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">Itinerario generado por IA</h5>
                  <button
                    className="btn btn-sm btn-light"
                    onClick={() =>
                      navigator.clipboard.writeText(
                        selectedItineraryDetail.generated_itinerary || ""
                      )
                    }
                  >
                    📋 Copiar
                  </button>
                </div>
                <div className="card-body">
                  {selectedItineraryDetail.status === "completed" ? (
                    <div
                      style={{
                        whiteSpace: "pre-wrap",
                        lineHeight: "1.8",
                        fontSize: "0.95rem",
                      }}
                    >
                      {selectedItineraryDetail.generated_itinerary}
                    </div>
                  ) : (
                    <div className="alert alert-warning">
                      {selectedItineraryDetail.generated_itinerary ||
                        "No se pudo generar el itinerario"}
                    </div>
                  )}
                </div>
              </div>

              {/* Publicaciones usadas en el itinerario */}
              {selectedItineraryDetail.publications &&
                selectedItineraryDetail.publications.length > 0 && (
                  <div className="mb-3">
                    <h5 className="mb-3">
                      📍 Lugares incluidos en este itinerario
                    </h5>
                    <p className="text-muted mb-3">
                      Estos son los lugares de nuestra plataforma que la IA
                      utilizó para crear este itinerario:
                    </p>

                    <div className="row row-cols-1 row-cols-md-2 g-4">
                      {selectedItineraryDetail.publications.map((p) => (
                        <div className="col" key={p.id}>
                          <div
                            className="card shadow-sm h-100"
                            style={{ cursor: "pointer" }}
                            onClick={() => openPublicationDetail(p)}
                          >
                            <div className="card-body pb-0">
                              <div className="d-flex justify-content-between align-items-start">
                                <div className="flex-grow-1">
                                  <h6 className="mb-1">{p.place_name}</h6>
                                  <small className="text-muted">
                                    {p.address && `${p.address}, `}
                                    {p.city}, {p.province}
                                    {p.country ? `, ${p.country}` : ""}
                                  </small>
                                  <div className="mt-2 d-flex flex-wrap gap-2">
                                    <RatingBadge
                                      avg={p.rating_avg}
                                      count={p.rating_count}
                                    />
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
                              </div>
                            </div>

                            {p.photos?.length ? (
                              <div
                                id={`profile-itin-${p.id}`}
                                className="carousel slide mt-2"
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
                                          height: 220,
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
                                      data-bs-target={`#profile-itin-${p.id}`}
                                      data-bs-slide="prev"
                                      onClick={(e) => e.stopPropagation()}
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
                                      data-bs-target={`#profile-itin-${p.id}`}
                                      data-bs-slide="next"
                                      onClick={(e) => e.stopPropagation()}
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
                              <button
                                className="btn btn-sm btn-celeste"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openPublicationDetail(p);
                                }}
                              >
                                Ver detalles
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          </div>
        </div>
      )}


      {/* ⭐ Modal de detalles de publicación (igual que en Home.jsx) */}
      <PublicationDetailModal
        open={openDetailModal}
        pub={currentPub}
        token={token}
        me={me}
        onClose={() => setOpenDetailModal(false)}
        onToggleFavorite={() => { }} // desde el perfil no tocamos estado de favoritos
      />
    </div>
  );
}
