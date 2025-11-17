// src/pages/SearchUsers.jsx
import React, { useMemo, useState } from "react";

// 🔹 Datos de ejemplo (después podés reemplazar por datos reales del backend)
const MOCK_TRAVELERS = [
  {
    id: 1,
    username: "agus.viajes",
    name: "Agustina",
    city: "Buenos Aires, Argentina",
    destinations: ["Europa", "París", "Roma"],
    style: "Low cost & cultural",
    budget: "$$",
    about: "Me encantan las ciudades con historia, los museos y los cafés lindos.",
    matchesWithYou: 92,
    tags: ["Museos", "Café", "Caminatas", "Hostels"]
  },
  {
    id: 2,
    username: "viajero.nomade",
    name: "Nicolás",
    city: "Córdoba, Argentina",
    destinations: ["Sudeste Asiático", "Tailandia"],
    style: "Mochilero",
    budget: "$",
    about: "Busco gente para viajes largos, poca planificación y mucha aventura.",
    matchesWithYou: 78,
    tags: ["Backpacking", "Playas", "Street food"]
  },
  {
    id: 3,
    username: "city.breaks",
    name: "Valen",
    city: "Montevideo, Uruguay",
    destinations: ["Europa", "Madrid", "Londres"],
    style: "City break",
    budget: "$$$",
    about: "Amo las escapadas cortas, los buenos restaurantes y los barrios con encanto.",
    matchesWithYou: 84,
    tags: ["Restaurantes", "Airbnb", "Mercados"]
  },
  {
    id: 4,
    username: "familia.onboard",
    name: "Mariana",
    city: "Rosario, Argentina",
    destinations: ["Brasil", "Caribe"],
    style: "En familia",
    budget: "$$",
    about: "Viajo con niños, busco planes tranquilos y alojamientos cómodos.",
    matchesWithYou: 66,
    tags: ["Niños", "All inclusive", "Playa"]
  },
  {
    id: 5,
    username: "solo.traveler",
    name: "Sofi",
    city: "Santiago, Chile",
    destinations: ["Europa", "Lisboa", "Barcelona"],
    style: "Solo traveler",
    budget: "$$",
    about: "Me gusta viajar sola pero compartir algunos planes con otras personas.",
    matchesWithYou: 81,
    tags: ["Co-working", "Cafés", "Tours a pie"]
  }
];

export default function SearchUsers({ me }) {
  const [searchText, setSearchText] = useState("");
  const [filterDestination, setFilterDestination] = useState("todos");
  const [filterStyle, setFilterStyle] = useState("todos");

  const filteredTravelers = useMemo(() => {
    return MOCK_TRAVELERS.filter((t) => {
      // filtro por texto (nombre, usuario, destinos, tags)
      const text = searchText.toLowerCase();
      const matchesText =
        !text ||
        t.username.toLowerCase().includes(text) ||
        t.name.toLowerCase().includes(text) ||
        t.destinations.join(" ").toLowerCase().includes(text) ||
        t.tags.join(" ").toLowerCase().includes(text);

      // filtro por destino "macro"
      const matchesDestination =
        filterDestination === "todos" ||
        t.destinations.some((d) =>
          d.toLowerCase().includes(filterDestination.toLowerCase())
        );

      // filtro por estilo
      const matchesStyle =
        filterStyle === "todos" ||
        t.style.toLowerCase().includes(filterStyle.toLowerCase());

      return matchesText && matchesDestination && matchesStyle;
    });
  }, [searchText, filterDestination, filterStyle]);

  return (
    <div className="container-fluid py-4">
      {/* Cabecera */}
      <div className="mb-4 px-1">
        <h1 className="h3 fw-bold d-flex align-items-center mb-1">
          <span className="me-2">👥</span>
          Buscar otros viajeros
        </h1>
        <p className="text-muted mb-0">
          Encontrá personas con intereses y estilos de viaje parecidos a los tuyos
          para compartir experiencias, tips o itinerarios.
        </p>
        {me?.username && (
          <p className="text-muted mt-1 mb-0 small">
            Estás buscando como <strong>@{me.username}</strong>
          </p>
        )}
      </div>

      {/* Buscador + filtros */}
      <div className="card shadow-sm mb-4 rounded-4 border-0">
        <div className="card-body">
          <div className="row g-3 align-items-end">
            <div className="col-md-6">
              <label className="form-label fw-semibold">Buscar por nombre, usuario o palabra clave</label>
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
              <label className="form-label fw-semibold">Destino de interés</label>
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
              {filteredTravelers.length === 0
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
                    <div className="small text-muted">
                      📍 {t.city}
                    </div>
                  </div>
                </div>

                {/* Destinos / estilo */}
                <div className="mb-2">
                  <div className="small text-muted mb-1">
                    Destinos favoritos:
                  </div>
                  <div className="d-flex flex-wrap gap-1 mb-2">
                    {t.destinations.map((d) => (
                      <span
                        key={d}
                        className="badge bg-light text-secondary border"
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                  <span className="badge bg-primary bg-opacity-10 text-primary small me-2">
                    ✈️ {t.style}
                  </span>
                  <span className="badge bg-success bg-opacity-10 text-success small">
                    Presupuesto {t.budget}
                  </span>
                </div>

                {/* About */}
                <p className="small text-muted flex-grow-1 mb-2">
                  {t.about}
                </p>

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
                </div>

                {/* Match + botón */}
                <div className="d-flex justify-content-between align-items-center mt-2">
                  <div className="d-flex align-items-center gap-1">
                    <span className="small text-muted">Coincidencia</span>
                    <span className="fw-semibold text-success">
                      {t.matchesWithYou}%
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary rounded-pill px-3"
                    disabled
                  >
                    Ver perfil
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {filteredTravelers.length === 0 && (
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
