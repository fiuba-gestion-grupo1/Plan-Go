import React from "react";
import PhotoCarousel from "./PhotoCarousel";
import { StatusBadge, RatingBadge } from "./UIComponents";
import { PublicationAvailability } from "./AvailabilityComponents";

export default function PublicationCard({
  publication,
  carouselPrefix = "carousel",
  showStatus = false,
  showRating = false,
  showFavorite = false,
  showActions = false,
  isFavorite = false,
  onToggleFavorite,
  actions = null,
  footer = null,
  showDetails = false,
}) {
  const p = publication;

  return (
    <div
      className={`card shadow-sm h-100 ${p.status === "deleted" ? "border-dark" : ""}`}
    >
      <div className="card-body pb-0">
        <div className="d-flex justify-content-between align-items-start mb-2">
          <div className="flex-grow-1">
            <h5 className="card-title mb-1">{p.place_name}</h5>
            <small className="text-muted d-block">
              {p.address}, {p.city}, {p.province}, {p.country}
            </small>
          </div>

          <div className="d-flex flex-column align-items-end gap-2">
            {showStatus && <StatusBadge status={p.status} />}

            {showRating && p.avg_rating != null && (
              <RatingBadge avg={p.avg_rating} count={p.review_count || 0} />
            )}

            {showFavorite && (
              <button
                className="btn btn-sm btn-link p-0"
                onClick={() => onToggleFavorite?.(p.id)}
                title={
                  isFavorite ? "Quitar de favoritos" : "Agregar a favoritos"
                }
              >
                <span
                  style={{
                    fontSize: "1.5rem",
                    color: isFavorite ? "red" : "#ccc",
                  }}
                >
                  {isFavorite ? "❤️" : "🤍"}
                </span>
              </button>
            )}

            {showActions && actions}
          </div>
        </div>

        <PublicationAvailability publication={p} />
      </div>

      <PhotoCarousel
        photos={p.photos}
        publicationId={p.id}
        carouselPrefix={carouselPrefix}
      />

      {(footer ||
        showDetails ||
        ((p.status === "rejected" || p.status === "deleted") &&
          p.rejection_reason)) && (
        <div className="card-footer bg-white">
          {showDetails && (
            <small className="text-muted d-block">
              {p.created_at &&
                `Creado: ${new Date(p.created_at).toLocaleString()}`}
            </small>
          )}

          {p.status === "rejected" && p.rejection_reason && (
            <small className="text-danger d-block mt-1">
              ❌ <strong>Motivo:</strong> {p.rejection_reason}
            </small>
          )}

          {p.status === "deleted" && p.rejection_reason && (
            <small className="text-dark d-block mt-1">
              🗑️ <strong>Motivo:</strong> {p.rejection_reason}
            </small>
          )}

          {footer}
        </div>
      )}
    </div>
  );
}
