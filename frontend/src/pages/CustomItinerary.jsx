import React, { useState, useEffect } from 'react';
import { request } from '../utils/api';
import { PublicationAvailability, DurationBadge } from '../components/shared/AvailabilityComponents';

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

  // Convertir tiempo a minutos desde medianoche
  const timeToMinutes = (timeStr) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
  };

  // Convertir minutos a formato HH:MM
  const minutesToTime = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
  };

  // Obtener todos los slots de tiempo en orden
  const getAllTimeSlots = () => {
    return [...timeSlots.morning, ...timeSlots.afternoon, ...timeSlots.evening];
  };

  // Calcular slots que debe ocupar una actividad según su duración
  const calculateOccupiedSlots = (startTime, durationMinutes) => {
    const allSlots = getAllTimeSlots();
    const startIndex = allSlots.indexOf(startTime);
    if (startIndex === -1) return [startTime];

    const slotsNeeded = Math.ceil(durationMinutes / 30); // Cada slot es de 30 min
    const occupiedSlots = [];
    
    for (let i = 0; i < slotsNeeded && (startIndex + i) < allSlots.length; i++) {
      occupiedSlots.push(allSlots[startIndex + i]);
    }
    
    return occupiedSlots;
  };

  // Determinar período de un tiempo específico
  const getPeriodForTime = (time) => {
    if (timeSlots.morning.includes(time)) return 'morning';
    if (timeSlots.afternoon.includes(time)) return 'afternoon';
    if (timeSlots.evening.includes(time)) return 'evening';
    return 'morning'; // default
  };

  // Calcular duración inteligente basada en categorías
  const getSmartDuration = (publication) => {
    if (publication.duration_min && publication.duration_min > 0) {
      return publication.duration_min;
    }

    // Duraciones por defecto basadas en categorías comunes
    const categories = publication.categories || [];
    const categoryDurations = {
      'museo': 180,        // 3 horas
      'restaurante': 90,   // 1.5 horas  
      'teatro': 150,       // 2.5 horas
      'cine': 120,         // 2 horas
      'parque': 240,       // 4 horas
      'playa': 300,        // 5 horas
      'shopping': 180,     // 3 horas
      'mercado': 120,      // 2 horas
      'iglesia': 60,       // 1 hora
      'mirador': 90,       // 1.5 horas
      'bar': 120,          // 2 horas
      'cafe': 60,          // 1 hora
      'aventura': 240,     // 4 horas
      'deportes': 180,     // 3 horas
      'spa': 180,          // 3 horas
      'cultura': 150,      // 2.5 horas
      'gastronomia': 90,   // 1.5 horas
      'vida-nocturna': 180 // 3 horas
    };

    // Buscar duración basada en categorías
    for (const category of categories) {
      const categoryLower = (typeof category === 'string' ? category : category.slug || category.name || '').toLowerCase();
      if (categoryDurations[categoryLower]) {
        return categoryDurations[categoryLower];
      }
    }

    // Duración por defecto
    return 120; // 2 horas
  };

  // Agregar publicación a un slot (actualizado para usar duración inteligente)
  function addPublicationToSlot(publication) {
    if (!selectedSlot) return;

    const { dayKey, period, time } = selectedSlot;
    
    // Calcular duración usando lógica inteligente
    const durationMinutes = getSmartDuration(publication);
    const occupiedSlots = calculateOccupiedSlots(time, durationMinutes);
    
    // Verificar si hay conflictos con actividades existentes
    const hasConflict = occupiedSlots.some(slotTime => {
      const slotPeriod = getPeriodForTime(slotTime);
      return itineraryData.itinerary[dayKey][slotPeriod][slotTime] !== null;
    });

    if (hasConflict) {
      alert('Esta actividad se superpone con otra ya programada. Por favor, elige otro horario.');
      return;
    }

    // Agregar la actividad principal al slot seleccionado
    const activityData = {
      ...publication,
      duration_min: durationMinutes,
      start_time: time,
      is_main_slot: true
    };

    // Marcar todos los slots ocupados
    setItineraryData(prev => {
      const newItinerary = { ...prev.itinerary };
      
      occupiedSlots.forEach(slotTime => {
        const slotPeriod = getPeriodForTime(slotTime);
        newItinerary[dayKey] = {
          ...newItinerary[dayKey],
          [slotPeriod]: {
            ...newItinerary[dayKey][slotPeriod],
            [slotTime]: slotTime === time ? activityData : {
              ...publication,
              duration_min: durationMinutes,
              start_time: time,
              is_continuation: true,
              main_slot_time: time
            }
          }
        };
      });
      
      return { ...prev, itinerary: newItinerary };
    });

    // Actualizar selected publications para todos los slots ocupados
    setSelectedPublications(prev => {
      const newSelected = { ...prev };
      occupiedSlots.forEach(slotTime => {
        const slotPeriod = getPeriodForTime(slotTime);
        newSelected[`${dayKey}-${slotPeriod}-${slotTime}`] = slotTime === time ? activityData : {
          ...publication,
          is_continuation: true,
          main_slot_time: time
        };
      });
      return newSelected;
    });

    setShowPublicationModal(false);
    setSelectedSlot(null);
  }

  // Remover publicación de un slot
  function removePublicationFromSlot(dayKey, period, time) {
    const currentActivity = itineraryData.itinerary[dayKey][period][time];
    if (!currentActivity) return;

    // Determinar el tiempo de inicio principal
    const mainStartTime = currentActivity.is_continuation ? currentActivity.main_slot_time : time;
    
    // Si es una continuación, encontrar la actividad principal
    let mainActivity = currentActivity;
    if (currentActivity.is_continuation) {
      // Buscar la actividad principal
      const mainPeriod = getPeriodForTime(mainStartTime);
      mainActivity = itineraryData.itinerary[dayKey][mainPeriod][mainStartTime];
    }

    if (mainActivity && mainActivity.duration_min) {
      // Calcular todos los slots ocupados por esta actividad
      const occupiedSlots = calculateOccupiedSlots(mainStartTime, mainActivity.duration_min);
      
      // Limpiar todos los slots ocupados
      setItineraryData(prev => {
        const newItinerary = { ...prev.itinerary };
        
        occupiedSlots.forEach(slotTime => {
          const slotPeriod = getPeriodForTime(slotTime);
          newItinerary[dayKey] = {
            ...newItinerary[dayKey],
            [slotPeriod]: {
              ...newItinerary[dayKey][slotPeriod],
              [slotTime]: null
            }
          };
        });
        
        return { ...prev, itinerary: newItinerary };
      });

      // Actualizar selected publications
      setSelectedPublications(prev => {
        const newSelected = { ...prev };
        occupiedSlots.forEach(slotTime => {
          const slotPeriod = getPeriodForTime(slotTime);
          delete newSelected[`${dayKey}-${slotPeriod}-${slotTime}`];
        });
        return newSelected;
      });
    } else {
      // Remover solo el slot actual (actividad sin duración)
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
      
      // Resetear para comenzar un nuevo itinerario o navegar
      setStep('setup');
      setDestination('');
      setStartDate('');
      setEndDate('');
      setItineraryData(null);
      setSelectedPublications({});
      setError('');
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
                              <div className={`card h-100 ${publication ? (publication.is_continuation ? 'border-warning bg-warning bg-opacity-10' : 'border-success bg-light') : 'border-light'}`}>
                                <div className="card-body p-3">
                                  <div className="d-flex align-items-center justify-content-between mb-2">
                                    <strong className="text-primary">{time}</strong>
                                    {publication && !publication.is_continuation && (
                                      <button
                                        className="btn btn-sm btn-outline-danger"
                                        onClick={() => removePublicationFromSlot(dayKey, period, time)}
                                        title="Remover actividad completa"
                                      >
                                        ×
                                      </button>
                                    )}
                                  </div>
                                  
                                  {publication ? (
                                    <div>
                                      {publication.is_continuation ? (
                                        <div className="text-center text-muted">
                                          <small>
                                            <em>↳ Continuación de:</em>
                                            <br />
                                            <strong>{publication.place_name}</strong>
                                            <br />
                                            <small>Inicio: {publication.start_time || publication.main_slot_time}</small>
                                          </small>
                                        </div>
                                      ) : (
                                        <>
                                          <div className="mb-1">
                                            <strong>{publication.place_name}</strong>
                                          </div>
                                          <small className="text-muted">
                                            📍 {publication.address}
                                          </small>
                                          {publication.duration_min && (
                                            <div className="mt-1">
                                              <span className="badge bg-info text-white">
                                                {Math.floor(publication.duration_min / 60)}h {publication.duration_min % 60}m
                                              </span>
                                            </div>
                                          )}
                                          {publication.categories && publication.categories.length > 0 && (
                                            <div className="mt-1">
                                              {publication.categories.slice(0, 2).map(cat => (
                                                <span key={cat} className="badge bg-secondary me-1 small">
                                                  {cat}
                                                </span>
                                              ))}
                                            </div>
                                          )}
                                        </>
                                      )}
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
                            className="card h-100 border-primary hover-card"
                            style={{ cursor: 'pointer' }}
                            onClick={() => addPublicationToSlot(pub)}
                          >
                            {pub.photos && pub.photos.length > 0 && (
                              <img 
                                src={pub.photos[0]} 
                                className="card-img-top"
                                alt={pub.place_name}
                                style={{ height: '150px', objectFit: 'cover' }}
                              />
                            )}
                            <div className="card-body">
                              <h6 className="card-title">{pub.place_name}</h6>
                              <p className="card-text small text-muted mb-2">
                                📍 {pub.address}
                              </p>
                              <p className="card-text small mb-2">
                                🌎 {pub.city}, {pub.province}, {pub.country}
                              </p>
                              {pub.rating_avg && pub.rating_avg > 0 && (
                                <p className="card-text small mb-2">
                                  ⭐ {pub.rating_avg.toFixed(1)} ({pub.rating_count || 0} reseñas)
                                </p>
                              )}
                              {/* Mostrar duración estimada */}
                              <DurationBadge durationMin={pub.duration_min} />
                              {pub.categories && pub.categories.length > 0 && (
                                <div className="mb-2">
                                  {pub.categories.map((cat, idx) => (
                                    <span key={idx} className="badge bg-secondary me-1">
                                      {typeof cat === 'string' ? cat : cat.name || cat.slug}
                                    </span>
                                  ))}
                                </div>
                              )}
                              {/* Información de disponibilidad */}
                              <PublicationAvailability publication={pub} />
                            </div>
                            <div className="card-footer text-center">
                              <small className="text-primary">
                                Haz clic para agregar
                              </small>
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

  return (
    <>
      {/* El resto del componente estará aquí */}
      <style>{`
        .hover-card {
          transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        
        .hover-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        }
      `}</style>
      {null}
    </>
  );
}