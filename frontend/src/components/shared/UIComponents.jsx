import React from "react";

export function Stars({ value = 0 }) {
  const pct = Math.max(0, Math.min(100, (Number(value) / 5) * 100));
  return (
    <span className="position-relative" aria-label={`Rating ${value}/5`}>
      <span className="text-muted" style={{ letterSpacing: 1 }}>
        ★★★★★
      </span>
      <span
        className="position-absolute top-0 start-0 overflow-hidden"
        style={{ width: `${pct}%` }}
      >
        <span className="text-warning" style={{ letterSpacing: 1 }}>
          ★★★★★
        </span>
      </span>
    </span>
  );
}

export function RatingBadge({ avg = 0, count = 0 }) {
  return (
    <span className="badge bg-light text-dark border">
      <Stars value={avg} />
      <span className="ms-1">
        {Number(avg).toFixed(1)} • {count} reseña{count === 1 ? "" : "s"}
      </span>
    </span>
  );
}

export function StatusBadge({ status }) {
  const badges = {
    approved: { text: "✓ Aprobada", className: "bg-success" },
    pending: { text: "⏳ Pendiente", className: "bg-warning text-dark" },
    rejected: { text: "✗ Rechazada", className: "bg-danger" },
    deleted: { text: "🗑️ Eliminada", className: "bg-dark" },
  };

  const badge = badges[status] || { text: status, className: "bg-secondary" };

  return <span className={`badge ${badge.className}`}>{badge.text}</span>;
}

export function LoadingSpinner({ message = "Cargando..." }) {
  return <div className="alert alert-info">{message}</div>;
}

export function ErrorAlert({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div
      className="alert alert-danger alert-dismissible fade show"
      role="alert"
    >
      {message}
      {onDismiss && (
        <button
          type="button"
          className="btn-close"
          onClick={onDismiss}
          aria-label="Close"
        ></button>
      )}
    </div>
  );
}

export function SuccessAlert({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div
      className="alert alert-success alert-dismissible fade show"
      role="alert"
    >
      {message}
      {onDismiss && (
        <button
          type="button"
          className="btn-close"
          onClick={onDismiss}
          aria-label="Close"
        ></button>
      )}
    </div>
  );
}

export function EmptyState({ message, icon = "📭" }) {
  return (
    <div className="alert alert-secondary mt-3 text-center">
      <div className="fs-1 mb-2">{icon}</div>
      {message}
    </div>
  );
}
