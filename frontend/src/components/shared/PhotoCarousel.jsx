import React from "react";

export default function PhotoCarousel({ 
  photos = [], 
  publicationId, 
  height = 260,
  carouselPrefix = "carousel"
}) {
  if (!photos || photos.length === 0) {
    return (
      <div className="p-4 text-center text-muted" style={{ height }}>
        Sin fotos
      </div>
    );
  }

  const carouselId = `${carouselPrefix}-${publicationId}`;

  return (
    <div id={carouselId} className="carousel slide" data-bs-ride="false">
      <div className="carousel-inner">
        {photos.map((url, idx) => (
          <div className={`carousel-item ${idx === 0 ? "active" : ""}`} key={url}>
            <img
              src={url}
              className="d-block w-100"
              alt={`Foto ${idx + 1}`}
              style={{ height, objectFit: "cover" }}
            />
          </div>
        ))}
      </div>

      {photos.length > 1 && (
        <>
          <button
            className="carousel-control-prev"
            type="button"
            data-bs-target={`#${carouselId}`}
            data-bs-slide="prev"
            style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
          >
            <span className="carousel-control-prev-icon" aria-hidden="true" />
            <span className="visually-hidden">Anterior</span>
          </button>
          <button
            className="carousel-control-next"
            type="button"
            data-bs-target={`#${carouselId}`}
            data-bs-slide="next"
            style={{ filter: "drop-shadow(0 0 6px rgba(0,0,0,.4))" }}
          >
            <span className="carousel-control-next-icon" aria-hidden="true" />
            <span className="visually-hidden">Siguiente</span>
          </button>
        </>
      )}
    </div>
  );
}
