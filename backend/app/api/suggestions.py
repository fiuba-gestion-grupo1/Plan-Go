from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .auth import get_current_user
from .. import models

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])
# Función para puntuar un destino según las preferencias del usuario, hace una relacion de preferencias clima y demas
def score(dest, pref):
    s = 0
    if pref.continents and dest.continent in pref.continents: s += 3
    if pref.climates and dest.climate in pref.climates: s += 2
    if pref.activities:
        s += len(set(pref.activities) & set(dest.activities or []))  # +1 por match
    if pref.budget_max and getattr(dest, "cost_per_day", None):
        s += 2 if dest.cost_per_day <= pref.budget_max else 0
    if pref.duration_min_days and pref.duration_max_days and getattr(dest,"duration_days",None):
        if pref.duration_min_days <= dest.duration_days <= pref.duration_max_days:
            s += 1
    return s

@router.get("")
def get_suggestions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    pref = db.query(models.UserPreference).filter_by(user_id=user.id).first()
    if not pref:
        return []  # sin preferencias ⇒ sin ranking

    qs = db.query(models.Publication).all()

    ranked = sorted(qs, key=lambda d: score(d, pref), reverse=True)

    def _title_of(d):
        return getattr(d, "title", None) or getattr(d, "place_name", "") or f"Publicación #{d.id}"

    # 🔹 Filtrar solo las publicaciones con score > 0
    filtered = [d for d in ranked if score(d, pref) > 0]

    # 🔹 Tomar las top 10
    top10 = filtered[:10]

    return [
        {
            "id": d.id,
            "title": _title_of(d),
            "score": score(d, pref),
            "city": d.city,
            "province": d.province,
            "country": d.country,
            "rating_avg": getattr(d, "rating_avg", 0),
            "rating_count": getattr(d, "rating_count", 0),
            "photos": [p.url for p in (d.photos or [])],
        }
        for d in top10
    ]


## LA idea es que estos campos se puedan usar para sugerir destinos a los usuarios según sus preferencias.
## el tema es que tiene que haber una correlacion de campos o quizas con alguna IA ( mas dificil) para hacer el scoring de las sugerencias.
