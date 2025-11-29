import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ItineraryRequestForm from "../components/ItineraryRequestForm";
import { request } from "../utils/api";
import PublicationDetailModal from "../components/PublicationDetailModal";
import { RatingBadge, Stars } from "../components/shared/UIComponents";

export default function ItineraryRequest({ initialView = "form", me }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [myItineraries, setMyItineraries] = useState([]);
  const [showList, setShowList] = useState(initialView === "list");
  const [selectedItinerary, setSelectedItinerary] = useState(null);
  const token = localStorage.getItem("token") || "";

  const [deleteModal, setDeleteModal] = useState(false);
  const [itineraryToDelete, setItineraryToDelete] = useState(null);

  const [openDetailModal, setOpenDetailModal] = useState(false);
  const [currentPub, setCurrentPub] = useState(null);

  const isPremium = me?.role === "premium";

  useEffect(() => {
    if (initialView === "list") {
      fetchMyItineraries();
    }
  }, [initialView]);

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

  async function handleDeleteItinerary(itineraryId) {
    console.log(
      "🔥 ItineraryRequest: handleDeleteItinerary ejecutada con ID:",
      itineraryId,
    );
    setItineraryToDelete(itineraryId);
    setDeleteModal(true);
  }

  async function confirmDeleteItinerary() {
    if (!itineraryToDelete) return;

    setLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      await request(`/api/itineraries/${itineraryToDelete}`, {
        method: "DELETE",
        token,
      });

      setSuccessMsg("Itinerario eliminado exitosamente");

      if (selectedItinerary && selectedItinerary.id === itineraryToDelete) {
        setSelectedItinerary(null);
        setShowList(true);
      }

      await fetchMyItineraries();
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (e) {
      setError(e.message || "Error al eliminar el itinerario");
    } finally {
      setLoading(false);
      setDeleteModal(false);
      setItineraryToDelete(null);
    }
  }

  async function handleSubmit(payload) {
    setLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      const data = await request("/api/itineraries/request", {
        method: "POST",
        token,
        body: payload,
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

  function handleViewItineraries() {
    setShowList(true);
    setSelectedItinerary(null);
    fetchMyItineraries();
  }

  function handleNewRequest() {
    setShowList(false);
    setSelectedItinerary(null);
    setError("");
    setSuccessMsg("");
  }

  function handleViewItinerary(itinerary) {
    setSelectedItinerary(itinerary);
    setShowList(false);
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return "";

    const dateOnly = dateStr.split("T")[0];
    const [year, month, day] = dateOnly.split("-");

    const date = new Date(year, month - 1, day);

    return date.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  function openPublicationDetail(p) {
    setCurrentPub(p);
    setOpenDetailModal(true);
  }

  async function toggleFavorite(pubId) {
    try {
      const data = await request(`/api/publications/${pubId}/favorite`, {
        method: "POST",
        token,
      });
      setSelectedItinerary((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          publications: prev.publications.map((p) =>
            p.id === pubId ? { ...p, is_favorite: data.is_favorite } : p,
          ),
        };
      });
      if (currentPub && currentPub.id === pubId) {
        setCurrentPub((prev) => ({ ...prev, is_favorite: data.is_favorite }));
      }
    } catch (e) {
      setError(e.message || "Error al actualizar favorito");
    }
  }

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
                    {itinerary.status === "completed" && (
                      <span className="badge bg-success">Completado</span>
                    )}
                    {itinerary.status === "pending" && (
                      <span className="badge bg-warning text-dark">
                        Pendiente
                      </span>
                    )}
                    {itinerary.status === "failed" && (
                      <span className="badge bg-danger">Error</span>
                    )}
                  </div>

                  <p className="text-muted small mb-2">
                    {formatDate(itinerary.start_date)} -{" "}
                    {formatDate(itinerary.end_date)}
                  </p>

                  <p>
                    <strong>Tipo:</strong> {itinerary.trip_type}
                  </p>
                  <p>
                    <strong>Presupuesto:</strong> US${itinerary.budget}
                  </p>
                  <p>
                    <strong>Personas:</strong> {itinerary.cant_persons}
                  </p>

                  <div className="d-flex gap-2">
                    <button
                      className="btn btn-sm flex-grow-1"
                      onClick={() => handleViewItinerary(itinerary)}
                    >
                      Ver Itinerario
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={(e) => {
                        console.log(
                          "ItineraryRequest: Botón eliminar clickeado!",
                        );
                        console.log("Event:", e);
                        console.log("Itinerary ID:", itinerary.id);
                        e.stopPropagation();
                        handleDeleteItinerary(itinerary.id);
                      }}
                      title="Eliminar itinerario"
                      disabled={loading}
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <div className="card-footer text-muted small">
                  Creado:{" "}
                  {new Date(itinerary.created_at).toLocaleString("es-ES")}
                </div>
              </div>
            </div>
          ))}
        </div>

        {!loading && myItineraries.length === 0 && (
          <div className="alert alert-secondary">
            No tienes itinerarios generados aún. ¡Crea tu primer itinerario con
            IA!
          </div>
        )}
      </div>
    );
  }

  if (selectedItinerary) {
    return (
      <>
        <div className="container mt-4">
          <div className="d-flex align-items-center justify-content-between mb-4">
            <h3 className="mb-0">
              Itinerario: {selectedItinerary.destination}
            </h3>
            <div className="d-flex gap-2">
              <button
                className="btn btn-outline-secondary"
                onClick={handleViewItineraries}
              >
                Mis Itinerarios
              </button>
              {isPremium && (
                <button
                  className="btn btn-outline-custom"
                  onClick={() =>
                    navigate(`/itineraries/${selectedItinerary.id}/share`)
                  }
                  title="Compartir por mail"
                >
                  ✉️ Compartir por mail
                </button>
              )}
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
          {successMsg && (
            <div className="alert alert-success">{successMsg}</div>
          )}

          <div className="card shadow-sm mb-4">
            <div className="card-body">
              <div className="row mb-3">
                <div className="col-md-6">
                  <p>
                    <strong>Fechas:</strong>{" "}
                    {formatDate(selectedItinerary.start_date)} -{" "}
                    {formatDate(selectedItinerary.end_date)}
                  </p>
                  <p>
                    <strong>Tipo de viaje:</strong>{" "}
                    {selectedItinerary.trip_type}
                  </p>
                  <p>
                    <strong>Presupuesto:</strong> US${selectedItinerary.budget}
                  </p>
                  <p>
                    <strong>Personas:</strong> {selectedItinerary.cant_persons}
                  </p>
                </div>
                <div className="col-md-6">
                  {selectedItinerary.arrival_time && (
                    <p>
                      <strong>Hora de llegada:</strong>{" "}
                      {selectedItinerary.arrival_time}
                    </p>
                  )}
                  {selectedItinerary.departure_time && (
                    <p>
                      <strong>Hora de salida:</strong>{" "}
                      {selectedItinerary.departure_time}
                    </p>
                  )}
                  <p>
                    <strong>Estado:</strong>{" "}
                    {selectedItinerary.status === "completed" && (
                      <span className="badge bg-success">Completado</span>
                    )}
                    {selectedItinerary.status === "pending" && (
                      <span className="badge bg-warning text-dark">
                        Pendiente
                      </span>
                    )}
                    {selectedItinerary.status === "failed" && (
                      <span className="badge bg-danger">Error</span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="card shadow-sm">
            <div className="card-header text-white d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Itinerario Generado</h5>
              <button
                className="btn btn-sm btn-light"
                onClick={() =>
                  navigator.clipboard.writeText(
                    selectedItinerary.generated_itinerary || "",
                  )
                }
              >
                📋 Copiar
              </button>
            </div>
            <div className="card-body">
              {selectedItinerary.status === "completed" ? (
                <div
                  style={{
                    whiteSpace: "pre-wrap",
                    lineHeight: "1.8",
                    fontSize: "0.95rem",
                  }}
                >
                  {selectedItinerary.generated_itinerary}
                </div>
              ) : (
                <div className="alert alert-warning">
                  {selectedItinerary.generated_itinerary ||
                    "No se pudo generar el itinerario"}
                </div>
              )}
            </div>
          </div>

          {selectedItinerary.publications &&
            selectedItinerary.publications.length > 0 && (
              <div className="mt-4">
                <h4 className="mb-3">
                  📍 Lugares incluidos en este itinerario
                </h4>
                <p className="text-muted mb-3">
                  Estos son los lugares de nuestra plataforma que la IA utilizó
                  para crear tu itinerario:
                </p>

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
                              <h5 className="card-title mb-1">
                                {p.place_name}
                              </h5>
                              <small className="text-muted">
                                {p.address}, {p.city}, {p.province}, {p.country}
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

                            <button
                              className="btn btn-link p-0 ms-2"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleFavorite(p.id);
                              }}
                              style={{
                                fontSize: "1.5rem",
                                textDecoration: "none",
                              }}
                              title={
                                p.is_favorite
                                  ? "Quitar de favoritos"
                                  : "Agregar a favoritos"
                              }
                            >
                              {p.is_favorite ? "❤️" : "🤍"}
                            </button>
                          </div>
                        </div>

                        {p.photos?.length ? (
                          <div
                            id={`itin-carousel-${p.id}`}
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
                                  data-bs-target={`#itin-carousel-${p.id}`}
                                  data-bs-slide="prev"
                                >
                                  <span
                                    className="carousel-control-prev-icon"
                                    aria-hidden="true"
                                  />
                                </button>
                                <button
                                  className="carousel-control-next"
                                  type="button"
                                  data-bs-target={`#itin-carousel-${p.id}`}
                                  data-bs-slide="next"
                                >
                                  <span
                                    className="carousel-control-next-icon"
                                    aria-hidden="true"
                                  />
                                </button>
                              </>
                            )}
                          </div>
                        ) : (
                          <div className="p-4 text-center text-muted">
                            Sin fotos
                          </div>
                        )}

                        <div className="card-footer bg-white d-flex justify-content-between align-items-center">
                          <small className="text-muted">
                            Creado: {new Date(p.created_at).toLocaleString()}
                          </small>
                          <button
                            className="btn btn-sm btn-celeste"
                            onClick={(e) => {
                              e.stopPropagation();
                              openPublicationDetail(p);
                            }}
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

        <PublicationDetailModal
          open={openDetailModal}
          pub={currentPub}
          token={token}
          me={me || {}}
          onClose={() => setOpenDetailModal(false)}
          onToggleFavorite={toggleFavorite}
        />

        {deleteModal && (
          <div
            className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
            style={{ background: "rgba(0,0,0,.4)", zIndex: 1051 }}
          >
            <div
              className="bg-white rounded-3 shadow-lg border"
              style={{ maxWidth: 400, width: "90%" }}
            >
              <div className="p-4 text-center">
                <h5 className="mb-3">
                  ¿Estás seguro de que deseas eliminar este itinerario?
                </h5>
                <p className="text-muted mb-3">
                  Esta acción no se puede deshacer.
                </p>
                <div className="d-flex gap-2 justify-content-center">
                  <button
                    className="btn btn-outline-secondary"
                    onClick={() => setDeleteModal(false)}
                  >
                    Cancelar
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={confirmDeleteItinerary}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="container mt-4">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <div className="d-flex align-items-center justify-content-between mb-4">
            <h3 className="mb-0">Solicitar Nuevo Itinerario</h3>
            <button
              className="btn btn-outline-secondary"
              onClick={handleViewItineraries}
            >
              Mis Itinerarios
            </button>
          </div>

          {loading && (
            <div className="alert alert-info">Generando itinerario...</div>
          )}
          {error && <div className="alert alert-danger">{error}</div>}
          {successMsg && (
            <div className="alert alert-success">{successMsg}</div>
          )}

          <ItineraryRequestForm onSubmit={handleSubmit} isLoading={loading} />
        </div>
      </div>
    </div>
  );
}
