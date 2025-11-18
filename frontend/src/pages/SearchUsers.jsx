// src/pages/SearchUsers.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { request } from "../utils/api";

function SearchUsers({ me, onOpenMyProfile }) {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  const [searchText, setSearchText] = useState("");
  const [filterDestination, setFilterDestination] = useState("todos");
  const [filterStyle, setFilterStyle] = useState("todos");

  const [travelers, setTravelers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Cargar viajeros reales desde el backend
  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    async function loadTravelers() {
      setLoading(true);
      setError("");

      try {
        const data = await request("/api/users/travelers", { token });

        const list = Array.isArray(data) ? data : [];

        // Normalizo para que matchee la estructura de los mocks
        const normalized = list.map((u) => {
          const name = u.first_name || u.name || u.username || "Viajero";
          const city = [u.city, u.country].filter(Boolean).join(", ");

          return {
            id: u.id,
            username: u.username,
            name,
            city: city || "Sin ubicación",

            // destinos favoritos (pueden venir de distintos campos)
            destinations:
              u.favorite_destinations ||
              u.destinations ||
              u.top_destinations ||
              [],

            // estilo de viaje
            style:
              u.travel_style ||
              u.travel_profile ||
              u.travel_preference ||
              "",

            // nivel de presupuesto
            budget:
              u.budget_label ||
              (u.budget_level === 1
                ? "$"
                : u.budget_level === 2
                ? "$$"
                : u.budget_level === 3
                ? "$$$"
                : ""),

            // descripción / bio
            about:
              u.bio ||
              u.about ||
              "Todavía no completó la descripción de su perfil.",

            // tags: uso tags explícitas o las armo con preferencias
            tags:
              u.tags ||
              u.preference_tags || [
                ...(u.activities || []),
                ...(u.climates || []),
                ...(u.continents || []),
              ],

            // % de coincidencia (si el backend lo calcula)
            matchesWithYou:
              u.match_percentage ?? u.match_score ?? u.match ?? null,
          };
        });

        if (!cancelled) {
          setTravelers(normalized);
        }
      } catch (e) {
        if (!cancelled) {
          console.error("Error cargando viajeros", e);
          setError(e.message || "Error cargando otros viajeros.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadTravelers();

    return () => {
      cancelled = true;
    };
  }, [token]);

  // Filtros (idéntico a la versión con mocks, pero usando travelers reales)
  const filteredTravelers = useMemo(() => {
    const text = searchText.toLowerCase();

    return travelers.filter((t) => {
      const matchesText =
        !text ||
        t.username.toLowerCase().includes(text) ||
        t.name.toLowerCase().includes(text) ||
        t.destinations.join(" ").toLowerCase().includes(text) ||
        t.tags.join(" ").toLowerCase().includes(text);

      const matchesDestination =
        filterDestination === "todos" ||
        t.destinations.some((d) =>
          d.toLowerCase().includes(filterDestination.toLowerCase())
        );

      const matchesStyle =
        filterStyle === "todos" ||
        t.style.toLowerCase().includes(filterStyle.toLowerCase());

      return matchesText && matchesDestination && matchesStyle;
    });
  }, [searchText, filterDestination, filterStyle, travelers]);

  return (
    <div className="container-fluid py-4">
      {/* Cabecera */}
      <div className="mb-4 px-1">
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <h1 className="h3 fw-bold d-flex align-items-center mb-1">
              <span className="me-2">👥</span>
              Buscar otros viajeros
            </h1>
            <p className="text-muted mb-0">
              Encontrá personas con intereses y estilos de viaje parecidos a los
              tuyos para compartir experiencias, tips o itinerarios.
            </p>
            {me?.username && (
              <p className="text-muted mt-1 mb-0 small">
                Estás buscando como <strong>@{me.username}</strong>
              </p>
            )}
          </div>

          {onOpenMyProfile && (
            <button
              type="button"
              className="btn btn-outline-primary btn-sm rounded-pill ms-3"
              onClick={onOpenMyProfile}
            >
              🧳 Ver mi perfil viajero
            </button>
          )}
        </div>
      </div>

      {/* Errores / loading */}
      {error && (
        <div className="alert alert-danger py-2">
          {error || "Ocurrió un error al cargar los viajeros."}
        </div>
      )}

      {/* Buscador + filtros */}
      <div className="card shadow-sm mb-4 rounded-4 border-0">
        <div className="card-body">
          <div className="row g-3 align-items-end">
            <div className="col-md-6">
              <label className="form-label fw-semibold">
                Buscar por nombre, usuario o palabra clave
              </label>
              <div className="input-group">
                <span className="input-group-text">🔍</span>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Ej: París, mochilero, museos, café..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                />
              </div>
            </div>

            <div className="col-md-3">
              <label className="form-label fw-semibold">
                Destino de interés
              </label>
              <select
                className="form-select"
                value={filterDestination}
                onChange={(e) => setFilterDestination(e.target.value)}
              >
                <option value="todos">Cualquier destino</option>
                <option value="europa">Europa</option>
                <option value="brasil">Brasil</option>
                <option value="caribe">Caribe</option>
                <option value="sudeste asiático">Sudeste Asiático</option>
              </select>
            </div>

            <div className="col-md-3">
              <label className="form-label fw-semibold">Estilo de viaje</label>
              <select
                className="form-select"
                value={filterStyle}
                onChange={(e) => setFilterStyle(e.target.value)}
              >
                <option value="todos">Cualquiera</option>
                <option value="mochilero">Mochilero</option>
                <option value="low cost">Low cost</option>
                <option value="city break">City break</option>
                <option value="familia">En familia</option>
                <option value="solo">Solo traveler</option>
              </select>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center mt-3">
            <small className="text-muted">
              {loading
                ? "Cargando viajeros…"
                : filteredTravelers.length === 0
                ? "No encontramos viajeros con esos filtros."
                : `Se encontraron ${filteredTravelers.length} viajero${
                    filteredTravelers.length > 1 ? "s" : ""
                  }`}
            </small>
          </div>
        </div>
      </div>

      {/* Resultados */}
      <div className="row g-3">
        {filteredTravelers.map((t) => (
          <div key={t.id} className="col-12 col-md-6 col-lg-4">
            <div className="card traveler-card h-100 border-0 shadow-sm rounded-4">
              <div className="card-body d-flex flex-column">
                {/* Header con avatar + nombre */}
                <div className="d-flex align-items-center mb-2">
                  <div className="traveler-avatar me-3 d-flex align-items-center justify-content-center">
                    <span className="fw-bold text-white">
                      {t.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="fw-semibold">{t.name}</div>
                    <div className="small text-muted">@{t.username}</div>
                    <div className="small text-muted">📍 {t.city}</div>
                  </div>
                </div>

                {/* Destinos / estilo */}
                <div className="mb-2">
                  <div className="small text-muted mb-1">
                    Destinos favoritos:
                  </div>
                  <div className="d-flex flex-wrap gap-1 mb-2">
                    {t.destinations.length === 0 && (
                      <span className="badge bg-light text-secondary border">
                        Sin destinos cargados
                      </span>
                    )}
                    {t.destinations.map((d) => (
                      <span
                        key={d}
                        className="badge bg-light text-secondary border"
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                  {t.style && (
                    <span className="badge bg-primary bg-opacity-10 text-primary small me-2">
                      ✈️ {t.style}
                    </span>
                  )}
                  {t.budget && (
                    <span className="badge bg-success bg-opacity-10 text-success small">
                      Presupuesto {t.budget}
                    </span>
                  )}
                </div>

                {/* About */}
                <p className="small text-muted flex-grow-1 mb-2">{t.about}</p>

                {/* Tags */}
                <div className="mb-2 d-flex flex-wrap gap-1">
                  {t.tags.map((tag) => (
                    <span
                      key={tag}
                      className="badge rounded-pill bg-secondary bg-opacity-10 text-muted"
                    >
                      #{tag}
                    </span>
                  ))}
                  {t.tags.length === 0 && (
                    <span className="small text-muted">
                      Sin intereses etiquetados.
                    </span>
                  )}
                </div>

                {/* Match + botón */}
                <div className="d-flex justify-content-between align-items-center mt-2">
                  <div className="d-flex align-items-center gap-1">
                    <span className="small text-muted">Coincidencia</span>
                    <span className="fw-semibold text-success">
                      {t.matchesWithYou != null ? `${t.matchesWithYou}%` : "—"}
                    </span>
                  </div>
                  <Link
                    to={`/viajeros/${t.id}`} // 👈 coincide con la ruta de App.jsx
                    className="btn btn-sm btn-outline-primary rounded-pill px-3"
                  >
                    Ver perfil
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ))}

        {!loading && filteredTravelers.length === 0 && (
          <div className="col-12">
            <div className="alert alert-light border text-center">
              Probá ajustando los filtros o buscando por otra palabra clave. 🌍
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SearchUsers;
