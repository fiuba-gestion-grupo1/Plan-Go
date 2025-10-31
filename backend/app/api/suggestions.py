from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .auth import get_current_user
from .. import models, schemas

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])

# Función para puntuar un destino (esta no cambia)
def score(dest, pref):
    s = 0
    if pref.continents and dest.continent in pref.continents: s += 3
    if pref.climates and dest.climate in pref.climates: s += 2
    if pref.activities:
        s += len(set(pref.activities) & set(dest.activities or []))
    if pref.budget_max and getattr(dest, "cost_per_day", None):
        s += 2 if dest.cost_per_day <= pref.budget_max else 0
    if pref.duration_min_days and pref.duration_max_days and getattr(dest,"duration_days",None):
        if pref.duration_min_days <= dest.duration_days <= pref.duration_max_days:
            s += 1
    return s

@router.get("", response_model=List[schemas.PublicationOut])
def get_suggestions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    pref = db.query(models.UserPreference).filter_by(user_id=user.id).first()
    if not pref:
        return []

    base_query = db.query(models.Publication)

    if pref.publication_type and pref.publication_type != "all":
        base_query = base_query.join(models.Publication.categories).filter(models.Category.slug == pref.publication_type)

    qs = base_query.all()

    ranked = sorted(qs, key=lambda d: score(d, pref), reverse=True)
    filtered = [d for d in ranked if score(d, pref) > 0]
    top10 = filtered[:10]
    
    # Obtenemos los favoritos del usuario para el flag 'is_favorite'
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite).filter(models.Favorite.user_id == user.id).all()
    }

    # Obtenemos las solicitudes de borrado pendientes
    pending_deletion_ids = {
        req.publication_id
        for req in db.query(models.DeletionRequest).filter(
            models.DeletionRequest.status == "pending"
        ).all()
    }

    results: List[schemas.PublicationOut] = []
    for p in top10:
        results.append(
            schemas.PublicationOut(
                id=p.id,
                place_name=p.place_name,
                country=p.country,
                province=p.province,
                city=p.city,
                address=p.address,
                status=p.status,
                rejection_reason=getattr(p, "rejection_reason", None),
                created_by_user_id=p.created_by_user_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                
                # Conversión manual de las relaciones
                photos=[ph.url for ph in getattr(p, "photos", [])],
                categories=[c.slug for c in getattr(p, "categories", [])],

                # Ratings y taxonomía
                rating_avg=getattr(p, "rating_avg", 0.0) or 0.0,
                rating_count=getattr(p, "rating_count", 0) or 0,
                continent=getattr(p, "continent", None),
                climate=getattr(p, "climate", None),
                activities=getattr(p, "activities", []),
                cost_per_day=getattr(p, "cost_per_day", None),
                duration_days=getattr(p, "duration_days", None),
                
                # Flags
                is_favorite=p.id in favorite_ids,
                has_pending_deletion=p.id in pending_deletion_ids
            )
        )

    return results