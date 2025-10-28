from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
import os, re
from .. import models, schemas
from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/publications", tags=["publications"])

# --- helpers de permisos ---
def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    # Permití admin por rol o por username "admin" (como venías usando)
    if current_user.role != "admin" and current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return current_user

def require_premium(current_user: models.User = Depends(get_current_user)) -> models.User:
    # Solo usuarios "premium" pueden reseñar (como pediste)
    if current_user.role != "premium":
        raise HTTPException(status_code=403, detail="Solo usuarios premium pueden publicar reseñas")
    return current_user

def require_premium_or_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    # Útil si alguna vez querés que admin también pueda reseñar
    if current_user.role not in ("premium", "admin"):
        raise HTTPException(status_code=403, detail="Solo usuarios premium pueden publicar reseñas")
    return current_user

# --- Helpers mínimos para normalizar campos opcionales ---
_ALLOWED_CONTINENTS = {"américa", "europa", "asia", "áfrica", "oceanía"}

def _norm_text_or_none(s: Optional[str]) -> Optional[str]:
    s = (s or "").strip()
    return s or None

def _norm_continent(s: Optional[str]) -> Optional[str]:
    s = _norm_text_or_none(s)
    if not s:
        return None
    s = s.lower()
    # Acepta variantes simples
    aliases = {
        "america": "américa", "latam": "américa", "north america": "américa", "south america": "américa",
        "europe": "europa", "asia": "asia", "africa": "áfrica", "oceania": "oceanía", "australia": "oceanía"
    }
    s = aliases.get(s, s)
    return s if s in _ALLOWED_CONTINENTS else s  # no rechazo, solo normalizo

def _norm_climate(s: Optional[str]) -> Optional[str]:
    s = _norm_text_or_none(s)
    if not s:
        return None
    # Lo dejamos en minúsculas, sin validar duro (templado, tropical, etc.)
    return s.lower()

def _csv_to_list(csv_: Optional[str]) -> Optional[list]:
    csv_ = _norm_text_or_none(csv_)
    if not csv_:
        return None
    vals = [v.strip() for v in csv_.split(",")]
    vals = [v for v in vals if v]
    # normalizo a minúsculas para consistencia:
    return [v.lower() for v in vals] or None

UPLOAD_DIR = os.path.join("backend", "app", "static", "uploads", "publications")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _normalize_slug(s: str) -> str:
    return (s or "").strip().lower()

def _get_or_create_category(db: Session, slug: str, name: Optional[str] = None) -> models.Category:
    slug = _normalize_slug(slug)
    if not slug:
        raise HTTPException(status_code=400, detail="Categoría vacía")
    cat = db.query(models.Category).filter(models.Category.slug == slug).first()
    if cat:
        return cat
    cat = models.Category(slug=slug, name=name or slug.capitalize())
    db.add(cat)
    db.flush()
    return cat

@router.get("", response_model=List[schemas.PublicationOut])
def list_publications(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pubs = db.query(models.Publication).order_by(models.Publication.created_at.desc()).all()
    out: List[schemas.PublicationOut] = []
    for p in pubs:
        out.append(
            schemas.PublicationOut(
                id=p.id,
                place_name=p.place_name,
                country=p.country,
                province=p.province,
                city=p.city,
                address=p.address,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                rating_avg=getattr(p, "rating_avg", 0.0) or 0.0,
                rating_count=getattr(p, "rating_count", 0) or 0,
                categories=[c.slug for c in getattr(p, "categories", [])],
            )
        )
    return out

_STREET_NUM_RE = re.compile(r"\s*(.+?)\s+(\d+[A-Za-z\-]*)\s*$")

@router.post("", response_model=schemas.PublicationOut, status_code=status.HTTP_201_CREATED)
def create_publication(
    place_name: str = Form(...),
    country: str = Form(...),
    province: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    categories: Optional[str] = Form(None),  # CSV: aventura,cultura
    photos: Optional[List[UploadFile]] = File(None),

    # 🔹 NUEVOS CAMPOS (todos opcionales)
    continent: Optional[str] = Form(None),       # ej: europa / américa
    climate: Optional[str] = Form(None),         # ej: templado / tropical
    activities: Optional[str] = Form(None),      # CSV: playa,gastronomía
    cost_per_day: Optional[float] = Form(None),  # ej: 80.0
    duration_days: Optional[int] = Form(None),   # ej: 7

    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    files = photos or []
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Máximo 4 fotos por publicación")
    for f in files:
        if f.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Formato de imagen inválido (usa JPG/PNG/WebP)")

    # parseo básico de calle y número (legacy)
    street, number = address, None
    parts = address.strip().rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        street, number = parts[0], parts[1]

    # 🔹 Normalizaciones nuevas
    continent_norm  = _norm_continent(continent)
    climate_norm    = _norm_climate(climate)
    activities_list = _csv_to_list(activities)

    pub = models.Publication(
        place_name=place_name,
        name=place_name,
        country=country,
        province=province,
        city=city,
        address=address,
        street=street,
        created_at=datetime.now(timezone.utc),

        # 🔹 Seteo de los campos nuevos (si existen en tu modelo)
        continent=continent_norm if hasattr(models.Publication, "continent") else None,
        climate=climate_norm if hasattr(models.Publication, "climate") else None,
        activities=activities_list if hasattr(models.Publication, "activities") else None,
        cost_per_day=cost_per_day if hasattr(models.Publication, "cost_per_day") else None,
        duration_days=duration_days if hasattr(models.Publication, "duration_days") else None,
    )
    if hasattr(models.Publication, "number"):
        setattr(pub, "number", number)

    # categorías (opc)
    slugs: List[str] = []
    if categories:
        slugs = [_normalize_slug(s) for s in categories.split(",") if _normalize_slug(s)]
        for slug in slugs:
            cat = _get_or_create_category(db, slug)
            # requiere que tengas `categories = relationship("Category", secondary=publication_categories, ...)`
            pub.categories.append(cat)

    db.add(pub)
    db.flush()

    saved_urls: List[str] = []
    for idx, f in enumerate(files):
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(f.content_type, ".bin")
        filename = f"pub_{pub.id}_{idx}{ext}"
        abs_path = os.path.join(UPLOAD_DIR, filename)
        with open(abs_path, "wb") as out:
            out.write(f.file.read())
        url = f"/static/uploads/publications/{filename}"
        photo = models.PublicationPhoto(publication_id=pub.id, url=url, index_order=idx)
        db.add(photo)
        saved_urls.append(url)

    db.commit()
    db.refresh(pub)

    return schemas.PublicationOut(
        id=pub.id,
        place_name=pub.place_name,
        country=pub.country,
        province=pub.province,
        city=pub.city,
        address=pub.address,
        created_at=pub.created_at.isoformat() if pub.created_at else "",
        photos=saved_urls,
        rating_avg=getattr(pub, "rating_avg", 0.0) or 0.0,
        rating_count=getattr(pub, "rating_count", 0) or 0,
        categories=slugs if slugs else [c.slug for c in getattr(pub, "categories", [])],
    )

@router.delete("/{pub_id}", status_code=status.HTTP_200_OK)
def delete_publication(pub_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    for ph in pub.photos:
        filename = ph.url.split("/static/uploads/publications/")[-1]
        abs_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception:
            pass
    db.delete(pub)
    db.commit()
    return {"message": "Publicación eliminada"}

@router.get("/public", response_model=List[schemas.PublicationOut])
def list_publications_public(
    category: Optional[str] = Query(None, description="Slugs separados por coma, ej: aventura,cultura"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Publication)
    slugs: List[str] = []
    if category:
        slugs = [_normalize_slug(s) for s in category.split(",") if _normalize_slug(s)]
        if slugs:
            # join por la relación para evitar referenciar la tabla intermedia directamente
            q = q.join(models.Publication.categories).filter(models.Category.slug.in_(slugs)).distinct()

    pubs = q.order_by(models.Publication.created_at.desc()).all()
    out: List[schemas.PublicationOut] = []
    for p in pubs:
        out.append(
            schemas.PublicationOut(
                id=p.id,
                place_name=p.place_name,
                country=p.country,
                province=p.province,
                city=p.city,
                address=p.address,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                rating_avg=getattr(p, "rating_avg", 0.0) or 0.0,
                rating_count=getattr(p, "rating_count", 0) or 0,
                categories=[c.slug for c in getattr(p, "categories", [])],
            )
        )
    return out

def _update_publication_rating(db: Session, pub_id: int) -> None:
    avg_, count_ = db.query(func.avg(models.Review.rating), func.count(models.Review.id)) \
        .filter(models.Review.publication_id == pub_id).one()
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if hasattr(pub, "rating_avg"):
        pub.rating_avg = round(float(avg_ or 0.0), 1)
    if hasattr(pub, "rating_count"):
        pub.rating_count = int(count_ or 0)
    db.add(pub)

@router.post("/{pub_id}/reviews", response_model=schemas.ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    pub_id: int,
    payload: schemas.ReviewCreate,                # <-- Pydantic, evita dict crudo
    db: Session = Depends(get_db),
    user: models.User = Depends(require_premium), # <-- ahora sí existe
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    review = models.Review(
        publication_id=pub_id,
        author_id=user.id,
        rating=payload.rating,                     # validado (1..5) por Pydantic
        comment=(payload.comment or "").strip(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(review)
    db.flush()

    # Actualizar agregados si existen en el modelo
    try:
        _update_publication_rating(db, pub_id)
    except Exception:
        pass

    db.commit()
    db.refresh(review)

    return schemas.ReviewOut(
        id=review.id,
        rating=review.rating,
        comment=review.comment,
        author_username=user.username,
        created_at=review.created_at.isoformat()[:19],
    )

@router.get("/{pub_id}/reviews", response_model=list[schemas.ReviewOut])
def list_reviews(pub_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Review, models.User.username)
        .join(models.User, models.User.id == models.Review.author_id)
        .filter(models.Review.publication_id == pub_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
    out = []
    for r, username in rows:
        out.append(
            schemas.ReviewOut(
                id=r.id,
                rating=r.rating,
                comment=r.comment,
                author_username=username,
                created_at=r.created_at.isoformat()[:19],
            )
        )
    return out
