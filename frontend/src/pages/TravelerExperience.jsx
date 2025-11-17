import React from "react";

// Opciones del menú sin emojis
const menuOptions = [
  {
    title: "Mis Favoritos",
    description: "Accede a los lugares, actividades y posts que guardaste.",
    path: "favorites",
  },
  {
    title: "Mis Itinerarios Guardados",
    description: "Revisa y edita tus planes de viaje y rutas personalizadas.",
    path: "my-itineraries",
  },
  {
    title: "Mis Gastos",
    description: "Gestioná y visualizá el presupuesto y los costos de tus viajes.",
    path: "expenses",
  },
  {
    title: "Buscar Otros Viajeros",
    description: "Encontrá usuarios con intereses y destinos similares a los tuyos.",
    path: "search-travelers",
  },
];

const TravelerExperience = ({ onNavigate }) => {
  const handleNavigation = (path) => {
    if (onNavigate) onNavigate(path);
  };

  return (
    <div className="container-fluid py-4">
      
      {/* CABECERA SIN FONDO */}
      <div className="mb-4 px-1">
        <h1 className="h3 fw-bold d-flex align-items-center mb-1">
          <span className="me-2">🧭</span>
          Experiencia Viajera
        </h1>
        <p className="text-muted mb-0">
          Todo lo que necesitás para gestionar tus viajes y conectar con la comunidad.
        </p>
      </div>

      {/* OPCIONES */}
      <div className="row g-3">
        {menuOptions.map((opt, index) => (
          <div className="col-12 col-md-6" key={index}>
            <div
              className="card exp-card rounded-4 border-0 shadow-sm h-100 p-3"
              role="button"
              onClick={() => handleNavigation(opt.path)}
            >
              <h5 className="fw-semibold mb-1">{opt.title}</h5>
              <p className="text-muted small mb-0">{opt.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* FOOTER */}
      <div className="text-center text-muted small mt-4">
        ¡Plan&Go te acompaña en cada paso de tu aventura!
      </div>

    </div>
  );
};

export default TravelerExperience;
