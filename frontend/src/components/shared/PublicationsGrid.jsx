import React from "react";
import PublicationCard from "./PublicationCard";
import { LoadingSpinner, EmptyState } from "./UIComponents";

/**
 * Grid reutilizable para mostrar publicaciones
 */
export default function PublicationsGrid({
  publications = [],
  loading = false,
  emptyMessage = "No hay publicaciones.",
  emptyIcon = "📭",
  carouselPrefix = "carousel",
  showStatus = false,
  showRating = false,
  showFavorite = false,
  favorites = [],
  onToggleFavorite,
  renderActions = null,
  renderFooter = null,
  showDetails = false
}) {
  if (loading) {
    return <LoadingSpinner />;
  }

  if (publications.length === 0) {
    return <EmptyState message={emptyMessage} icon={emptyIcon} />;
  }

  return (
    <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
      {publications.map((pub) => {
        const isFavorite = favorites.includes(pub.id);
        
        return (
          <div className="col" key={pub.id}>
            <PublicationCard
              publication={pub}
              carouselPrefix={carouselPrefix}
              showStatus={showStatus}
              showRating={showRating}
              showFavorite={showFavorite}
              isFavorite={isFavorite}
              onToggleFavorite={onToggleFavorite}
              actions={renderActions?.(pub)}
              footer={renderFooter?.(pub)}
              showDetails={showDetails}
            />
          </div>
        );
      })}
    </div>
  );
}
