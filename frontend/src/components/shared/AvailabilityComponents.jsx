import React from 'react';

/**
 * Componente para mostrar días de la semana con indicadores visuales
 */
export function AvailabilityDays({ availableDays }) {
  const allDays = [
    { key: 'domingo', short: 'Dom', label: 'Domingo' },
    { key: 'lunes', short: 'Lun', label: 'Lunes' },
    { key: 'martes', short: 'Mar', label: 'Martes' },
    { key: 'miércoles', short: 'Mié', label: 'Miércoles' },
    { key: 'jueves', short: 'Jue', label: 'Jueves' },
    { key: 'viernes', short: 'Vie', label: 'Viernes' },
    { key: 'sábado', short: 'Sáb', label: 'Sábado' }
  ];

  if (!availableDays || availableDays.length === 0) {
    return null;
  }

  const normalizedAvailableDays = availableDays.map(day => day.toLowerCase().trim());

  return (
    <div className="mb-2">
      <small className="text-muted d-block mb-1">📅 Disponible:</small>
      <div className="d-flex gap-1 flex-wrap">
        {allDays.map(day => {
          const isAvailable = normalizedAvailableDays.includes(day.key.toLowerCase());
          return (
            <span
              key={day.key}
              className={`badge ${isAvailable ? 'bg-success' : 'bg-light text-muted'} small`}
              style={{ fontSize: '0.7rem', minWidth: '35px' }}
              title={day.label}
            >
              {day.short}
            </span>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Componente para mostrar horarios disponibles
 */
export function AvailabilityHours({ availableHours }) {
  if (!availableHours || availableHours.length === 0) {
    return null;
  }

  return (
    <div className="mb-2">
      <small className="text-muted d-block mb-1">🕐 Horarios:</small>
      <div className="d-flex gap-1 flex-wrap">
        {availableHours.map((hour, index) => (
          <span
            key={index}
            className="badge small"
            style={{ fontSize: '0.7rem', backgroundColor: '#3A92B5', color: 'white' }}
          >
            {hour}
          </span>
        ))}
      </div>
    </div>
  );
}

/**
 * Componente para mostrar duración formateada
 */
export function DurationBadge({ durationMin }) {
  if (!durationMin || durationMin <= 0) {
    return null;
  }

  const formatDuration = (minutes) => {
    if (minutes < 60) {
      return `${minutes} min`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      if (remainingMinutes === 0) {
        return `${hours}h`;
      } else {
        return `${hours}h ${remainingMinutes}m`;
      }
    }
  };

  return (
    <div className="mb-2">
      <span className="badge bg-info text-white" style={{ fontSize: '0.8rem' }}>
        ⏱️ {formatDuration(durationMin)}
      </span>
    </div>
  );
}

/**
 * Componente combinado para mostrar toda la información de disponibilidad
 */
export function PublicationAvailability({ publication }) {
  const { duration_min, available_days, available_hours } = publication;

  // Si no hay ninguna información de disponibilidad, no mostrar nada
  if (!duration_min && (!available_days || available_days.length === 0) && (!available_hours || available_hours.length === 0)) {
    return null;
  }

  return (
    <div className="availability-info mt-2 p-2 bg-light rounded">
      <DurationBadge durationMin={duration_min} />
      <AvailabilityDays availableDays={available_days} />
      <AvailabilityHours availableHours={available_hours} />
    </div>
  );
}