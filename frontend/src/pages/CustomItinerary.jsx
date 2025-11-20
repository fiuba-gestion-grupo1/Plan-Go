import React, { useState, useEffect } from 'react';
import { request } from '../utils/api';

export default function CustomItinerary({ me, token }) {
  const [step, setStep] = useState('setup'); // 'setup' | 'building'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Estados para el setup inicial
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [itineraryData, setItineraryData] = useState(null);

  // Estados para la construcción del itinerario
  const [availablePublications, setAvailablePublications] = useState([]);
  const [selectedPublications, setSelectedPublications] = useState({});
  const [showPublicationModal, setShowPublicationModal] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);

  // Horarios predefinidos
  const timeSlots = {
    morning: [
      '06:00', '06:30', '07:00', '07:30', '08:00', '08:30', 
      '09:00', '09:30', '10:00', '10:30', '11:00', '11:30'
    ],
    afternoon: [
      '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
      '15:00', '15:30', '16:00', '16:30', '17:00', '17:30'
    ],
    evening: [
      '18:00', '18:30', '19:00', '19:30', '20:00', '20:30',
      '21:00', '21:30', '22:00', '22:30', '23:00', '23:30'
    ]
  };

  const periodLabels = {
    morning: '🌅 MAÑANA (6:00 - 12:00)',
    afternoon: '🌞 TARDE (12:00 - 18:00)', 
    evening: '🌙 NOCHE (18:00 - 23:00)'
  };

  // Generar días entre fechas
  const generateDays = (start, end) => {
    const days = [];
    const startDate = new Date(start);
    const endDate = new Date(end);
    
    for (let d = startDate; d <= endDate; d.setDate(d.getDate() + 1)) {
      days.push(new Date(d));
    }
    return days;
  };

  // Buscar publicaciones del destino
  async function fetchPublications(destination) {
    setLoading(true);
    try {
      const data = await request(`/api/publications/search?destination=${encodeURIComponent(destination)}`, { 
        token: localStorage.getItem('token')
      });
      setAvailablePublications(data || []);
    } catch (e) {
      setError('Error al cargar publicaciones del destino');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  // Manejar setup inicial
  async function handleSetupSubmit() {
    if (!destination || !startDate || !endDate) {
      setError('Por favor completa todos los campos');
      return;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (start >= end) {
      setError('La fecha de inicio debe ser anterior a la fecha de fin');
      return;
    }

    const days = generateDays(startDate, endDate);
    
    if (days.length > 30) {
      setError('El itinerario no puede ser mayor a 30 días');
      return;
    }

    setError('');
    
    // Generar estructura del itinerario
    const itinerary = {};
    days.forEach(day => {
      const dayKey = day.toISOString().split('T')[0];
      itinerary[dayKey] = {
        morning: {},
        afternoon: {},
        evening: {}
      };
      
      // Inicializar todos los slots vacíos
      Object.keys(timeSlots).forEach(period => {
        timeSlots[period].forEach(time => {
          itinerary[dayKey][period][time] = null;
        });
      });
    });

    setItineraryData({ days, itinerary });
    await fetchPublications(destination);
    setStep('building');
  }

  // Agregar publicación a un slot
  function addPublicationToSlot(publication) {
    if (!selectedSlot) return;

    const { dayKey, period, time } = selectedSlot;
    
    setItineraryData(prev => ({
      ...prev,
      itinerary: {
        ...prev.itinerary,
        [dayKey]: {
          ...prev.itinerary[dayKey],
          [period]: {
            ...prev.itinerary[dayKey][period],
            [time]: publication
          }
        }
      }
    }));

    setSelectedPublications(prev => ({
      ...prev,
      [`${dayKey}-${period}-${time}`]: publication
    }));

    setShowPublicationModal(false);
    setSelectedSlot(null);
  }

  // Remover publicación de un slot
  function removePublicationFromSlot(dayKey, period, time) {
    setItineraryData(prev => ({
      ...prev,
      itinerary: {
        ...prev.itinerary,
        [dayKey]: {
          ...prev.itinerary[dayKey],
          [period]: {
            ...prev.itinerary[dayKey][period],
            [time]: null
          }
        }
      }
    }));

    setSelectedPublications(prev => {
      const newSelected = { ...prev };
      delete newSelected[`${dayKey}-${period}-${time}`];
      return newSelected;
    });
  }

  // Formatear fecha para mostrar
  const formatDate = (date) => {
    return date.toLocaleDateString('es-ES', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Guardar itinerario
  async function saveItinerary() {
    setLoading(true);
    try {
      const payload = {
        destination,
        start_date: startDate,
        end_date: endDate,
        itinerary_data: itineraryData.itinerary,
        type: 'custom'
      };

      await request('/api/itineraries/custom', {
        method: 'POST',
        token: localStorage.getItem('token'),
        body: payload
      });

      alert('¡Itinerario personalizado guardado exitosamente!');
      // Reset o navegar a lista de itinerarios
    } catch (e) {
      setError('Error al guardar el itinerario');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  if (step === 'setup') {
    return (
      <div className="container mt-4">
        <div className="row justify-content-center">
          <div className="col-lg-6">
            <div className="text-center mb-4">
              <h3 className="mb-3">✏️ Crear Itinerario Personalizado</h3>
              <p className="text-muted">
                Configura los detalles básicos para comenzar a armar tu itinerario
              </p>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="card shadow-sm">
              <div className="card-body">
                <form onSubmit={(e) => { e.preventDefault(); handleSetupSubmit(); }}>
                  <div className="mb-3">
                    <label className="form-label">
                      <strong>📍 Destino</strong>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Ej: Buenos Aires, Argentina"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      required
                    />
                    <small className="text-muted">
                      Solo se mostrarán publicaciones de este destino
                    </small>
                  </div>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="mb-3">
                        <label className="form-label">
                          <strong>📅 Fecha de inicio</strong>
                        </label>
                        <input
                          type="date"
                          className="form-control"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          min={new Date().toISOString().split('T')[0]}
                          required
                        />
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="mb-3">
                        <label className="form-label">
                          <strong>📅 Fecha de fin</strong>
                        </label>
                        <input
                          type="date"
                          className="form-control"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          min={startDate || new Date().toISOString().split('T')[0]}
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="d-grid">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      {loading ? 'Preparando...' : 'Continuar'}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            <div className="text-center mt-3">
              <small className="text-muted">
                💡 Podrás agregar actividades personalizadas y elegir horarios específicos para cada día
              </small>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'building' && itineraryData) {
    return (
      <div className="container mt-4">
        <div className="d-flex align-items-center justify-content-between mb-4">
          <div>
            <h3 className="mb-1">✏️ Itinerario Personalizado</h3>
            <p className="text-muted mb-0">
              📍 {destination} • {itineraryData.days.length} día(s)
            </p>
          </div>
          <div className="d-flex gap-2">
            <button 
              className="btn btn-outline-secondary"
              onClick={() => setStep('setup')}
            >
              ← Volver a configuración
            </button>
            <button
              className="btn btn-success"
              onClick={saveItinerary}
              disabled={loading}
            >
              {loading ? 'Guardando...' : '💾 Guardar Itinerario'}
            </button>
          </div>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {/* Itinerario por días */}
        {itineraryData.days.map((day, dayIndex) => {
          const dayKey = day.toISOString().split('T')[0];
          const dayData = itineraryData.itinerary[dayKey];

          return (
            <div key={dayKey} className="mb-5">
              <div className="card shadow-sm">
                <div className="card-header bg-primary text-white">
                  <h5 className="mb-0">
                    DÍA {dayIndex + 1} - {formatDate(day)}
                  </h5>
                </div>
                <div className="card-body">
                  {/* Cada período del día */}
                  {Object.entries(periodLabels).map(([period, label]) => (
                    <div key={period} className="mb-4">
                      <h6 className="mb-3 border-bottom pb-2">{label}</h6>
                      
                      <div className="row g-2">
                        {timeSlots[period].map(time => {
                          const publication = dayData[period][time];
                          const slotKey = `${dayKey}-${period}-${time}`;
                          
                          return (
                            <div key={time} className="col-md-6 col-lg-4">
                              <div className="card border-light h-100">
                                <div className="card-body p-3">
                                  <div className="d-flex align-items-center justify-content-between mb-2">
                                    <strong className="text-primary">{time}</strong>
                                    {publication && (
                                      <button
                                        className="btn btn-sm btn-outline-danger"
                                        onClick={() => removePublicationFromSlot(dayKey, period, time)}
                                        title="Remover actividad"
                                      >
                                        ×
                                      </button>
                                    )}
                                  </div>
                                  
                                  {publication ? (
                                    <div>
                                      <div className="mb-1">
                                        <strong>{publication.place_name}</strong>
                                      </div>
                                      <small className="text-muted">
                                        📍 {publication.address}
                                      </small>
                                    </div>
                                  ) : (
                                    <div className="text-center">
                                      <button
                                        className="btn btn-sm btn-outline-primary"
                                        onClick={() => {
                                          setSelectedSlot({ dayKey, period, time });
                                          setShowPublicationModal(true);
                                        }}
                                      >
                                        + Agregar actividad
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}

        {/* Modal para seleccionar publicación */}
        {showPublicationModal && (
          <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">
                    Agregar actividad para {selectedSlot?.time}
                  </h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => {
                      setShowPublicationModal(false);
                      setSelectedSlot(null);
                    }}
                  />
                </div>
                <div className="modal-body">
                  {loading ? (
                    <div className="text-center py-4">
                      <div className="spinner-border" role="status" />
                      <div>Cargando publicaciones...</div>
                    </div>
                  ) : availablePublications.length === 0 ? (
                    <div className="text-center py-4 text-muted">
                      <p>No hay publicaciones disponibles para "{destination}"</p>
                      <small>Intenta con un destino diferente</small>
                    </div>
                  ) : (
                    <div className="row g-3">
                      {availablePublications.map(pub => (
                        <div key={pub.id} className="col-md-6">
                          <div 
                            className="card h-100 border-primary"
                            style={{ cursor: 'pointer' }}
                            onClick={() => addPublicationToSlot(pub)}
                          >
                            <div className="card-body">
                              <h6 className="card-title">{pub.place_name}</h6>
                              <p className="card-text small text-muted mb-2">
                                📍 {pub.address}
                              </p>
                              {pub.categories && (
                                <div>
                                  {pub.categories.map(cat => (
                                    <span key={cat} className="badge bg-secondary me-1">
                                      {cat}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowPublicationModal(false);
                      setSelectedSlot(null);
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}