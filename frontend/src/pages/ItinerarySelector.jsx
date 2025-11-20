import React from 'react';

export default function ItinerarySelector({ onNavigate }) {
  return (
    <div className="container mt-4">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <div className="text-center mb-5">
            <h2 className="mb-3">🗺️ Generar Itinerario</h2>
            <p className="text-muted">
              Elige cómo quieres crear tu próximo itinerario de viaje
            </p>
          </div>

          <div className="row g-4">
            {/* Opción Personalizado */}
            <div className="col-md-6">
              <div className="card shadow-sm h-100 border-0 hover-card" style={{ cursor: 'pointer' }}>
                <div className="card-body text-center p-5">
                  <div className="mb-4" style={{ fontSize: '4rem' }}>
                    ✏️
                  </div>
                  <h4 className="card-title text-primary mb-3">Personalizado</h4>
                  <p className="card-text text-muted mb-4">
                    Crea tu itinerario paso a paso, agregando lugares específicos y 
                    organizando tu viaje según tus preferencias personales.
                  </p>
                  <div className="mb-4">
                    <small className="text-muted">
                      <strong>Incluye:</strong>
                      <br />
                      • Control total sobre el itinerario
                      <br />
                      • Selección manual de lugares
                      <br />
                      • Organización personalizada
                      <br />
                      • Gestión de tiempos y actividades
                    </small>
                  </div>
                  <button 
                    className="btn btn-outline-primary btn-lg"
                    onClick={() => onNavigate('itinerary-custom')}
                  >
                    Crear Personalizado
                  </button>
                </div>
              </div>
            </div>

            {/* Opción Con IA */}
            <div className="col-md-6">
              <div className="card shadow-sm h-100 border-0 hover-card" style={{ cursor: 'pointer' }}>
                <div className="card-body text-center p-5">
                  <div className="mb-4" style={{ fontSize: '4rem' }}>
                    🤖
                  </div>
                  <h4 className="card-title text-success mb-3">Con IA</h4>
                  <p className="card-text text-muted mb-4">
                    Deja que nuestra inteligencia artificial genere un itinerario 
                    completo basado en tus preferencias, presupuesto y fechas.
                  </p>
                  <div className="mb-4">
                    <small className="text-muted">
                      <strong>Incluye:</strong>
                      <br />
                      • Generación automática inteligente
                      <br />
                      • Recomendaciones personalizadas
                      <br />
                      • Optimización de rutas y tiempos
                      <br />
                      • Lugares verificados de la plataforma
                    </small>
                  </div>
                  <button 
                    className="btn btn-success btn-lg"
                    onClick={() => onNavigate('itinerary-ai')}
                  >
                    Generar con IA
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center mt-5">
            <div className="alert alert-light">
              <h6 className="mb-2">💡 ¿No sabes cuál elegir?</h6>
              <p className="mb-0 small text-muted">
                Si es tu primera vez, recomendamos usar <strong>Con IA</strong> para obtener 
                sugerencias inteligentes que puedes personalizar después.
              </p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .hover-card {
          transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        
        .hover-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
        }
      `}</style>
    </div>
  );
}