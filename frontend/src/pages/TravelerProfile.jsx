// src/pages/TravelerProfile.jsx
import React from "react";

export default function TravelerProfile({ me }) {
  // Nombre “bonito”
  const displayName = me?.full_name || me?.name || me?.username || "Viajero";
  const username = me?.username || "usuario";
  const location = me?.city || me?.country || "Agregá tu ciudad de origen";
  const bio =
    me?.bio ||
    "Contale a la comunidad qué te gusta cuando viajás: destinos favoritos, estilos de viaje, si preferís low cost, all inclusive, naturaleza, ciudades, etc.";

  // 🔹 Más adelante estos arrays los vamos a poblar con datos reales
  const publishedItineraries = []; // itinerarios que el usuario decide hacer públicos
  const favoritesToVisit = [];     // lugares favoritos - Por visitar
  const favoritesVisited = [];     // lugares favoritos - Visitados

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
            <button type="button" className="btn btn-outline-primary btn-sm" disabled>
              Editar perfil (próximamente)
            </button>
          </div>
        </div>
      </div>

      {/* Itinerarios publicados */}
      <div className="card border-0 shadow-sm rounded-4 mb-4">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h2 className="h5 fw-semibold mb-0">Itinerarios publicados</h2>
            <small className="text-muted">
              Estos son los itinerarios que otros viajeros pueden ver.
            </small>
          </div>

          {publishedItineraries.length === 0 ? (
            <div className="alert alert-light border mb-0">
              Todavía no publicaste ningún itinerario.
              <br />
              Más adelante vamos a listar acá los itinerarios que marques como
              <strong> públicos</strong> desde tu sección de viajes.
            </div>
          ) : (
            <ul className="list-group">
              {publishedItineraries.map((it) => (
                <li key={it.id} className="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <div className="fw-semibold">{it.name}</div>
                    <div className="small text-muted">
                      {it.destination} · {it.days} días
                    </div>
                  </div>
                  <button className="btn btn-sm btn-outline-primary">
                    Ver detalle
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Favoritos: Por visitar / Visitados */}
      <div className="row g-3">
        {/* Por visitar */}
        <div className="col-12 col-lg-6">
          <div className="card border-0 shadow-sm rounded-4 h-100">
            <div className="card-body">
              <h2 className="h6 fw-semibold mb-2">Lugares por visitar</h2>
              <small className="text-muted d-block mb-3">
                Lugares que te gustaría conocer y que querés mostrar a otros viajeros.
              </small>

              {favoritesToVisit.length === 0 ? (
                <div className="alert alert-light border mb-0 small">
                  Aún no agregaste lugares a <strong>Por visitar</strong>.
                  <br />
                  Después vamos a traer acá tus favoritos marcados como "Por visitar".
                </div>
              ) : (
                <ul className="list-group list-group-flush">
                  {favoritesToVisit.map((place) => (
                    <li key={place.id} className="list-group-item">
                      <div className="fw-semibold">{place.name}</div>
                      <div className="small text-muted">{place.location}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* Visitados */}
        <div className="col-12 col-lg-6">
          <div className="card border-0 shadow-sm rounded-4 h-100">
            <div className="card-body">
              <h2 className="h6 fw-semibold mb-2">Lugares visitados</h2>
              <small className="text-muted d-block mb-3">
                Lugares que ya visitaste y querés compartir como recomendación.
              </small>

              {favoritesVisited.length === 0 ? (
                <div className="alert alert-light border mb-0 small">
                  Aún no agregaste lugares a <strong>Visitados</strong>.
                  <br />
                  Después vamos a traer acá tus favoritos marcados como "Visitados".
                </div>
              ) : (
                <ul className="list-group list-group-flush">
                  {favoritesVisited.map((place) => (
                    <li key={place.id} className="list-group-item">
                      <div className="fw-semibold">{place.name}</div>
                      <div className="small text-muted">{place.location}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
