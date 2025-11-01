from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import os, re
from .. import models, schemas
from ..db import get_db
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/publications", tags=["publications"])

# Schema para rechazar o eliminar con motivo
class RejectRequest(BaseModel):
    reason: Optional[str] = None

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

@router.get("/all", response_model=List[schemas.PublicationOut])
def list_all_publications(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    # Mostrar TODAS las publicaciones (aprobadas, rechazadas, pendientes, eliminadas)
    pubs = (
        db.query(models.Publication)
        .order_by(models.Publication.created_at.desc())
        .all()
    )
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
                status=p.status,
                rejection_reason=getattr(p, "rejection_reason", None),
                created_by_user_id=p.created_by_user_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                rating_avg=getattr(p, "rating_avg", 0.0) or 0.0,
                rating_count=getattr(p, "rating_count", 0) or 0,
                categories=[c.slug for c in getattr(p, "categories", [])],
            )
        )
    return out

@router.get("", response_model=List[schemas.PublicationOut])
def list_publications(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    # Solo mostrar publicaciones APROBADAS en la lista principal (admin puede ver pendientes en /pending)
    pubs = (
        db.query(models.Publication)
        .filter(models.Publication.status == "approved")
        .order_by(models.Publication.created_at.desc())
        .all()
    )
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
                status=p.status,
                created_by_user_id=p.created_by_user_id,
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
    description: str = Form(...),
    categories: Optional[str] = Form(None),  # CSV: aventura,cultura
    photos: Optional[List[UploadFile]] = File(None),

    # 🔹 NUEVOS CAMPOS (todos opcionales)
    continent: Optional[str] = Form(None),       # ej: europa / américa
    climate: Optional[str] = Form(None),         # ej: templado / tropical
    activities: Optional[str] = Form(None),      # CSV: playa,gastronomía
    cost_per_day: Optional[float] = Form(None),  # ej: 80.0
    duration_days: Optional[int] = Form(None),   # ej: 7

    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
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

    # Crear con campos siempre presentes
    pub = models.Publication(
        place_name=place_name,
        name=place_name,
        country=country,
        province=province,
        city=city,
        address=address,
        description=description, # <-- AÑADIDO
        street=street,                       # compat con columna legacy 'street'
        status="approved",             # por defecto aprobado cuando lo crea un admin
        created_by_user_id=current_user.id,  # registrar quién lo creó
        created_at=datetime.now(timezone.utc),
    )
    if hasattr(models.Publication, "number"):
        setattr(pub, "number", number)

    # Setear condicionalmente ONLY si el atributo existe en el modelo
    if hasattr(pub, "continent"):
        pub.continent = continent_norm
    if hasattr(pub, "climate"):
        pub.climate = climate_norm
    if hasattr(pub, "activities"):
        pub.activities = activities_list
    if hasattr(pub, "cost_per_day"):
        pub.cost_per_day = cost_per_day
    if hasattr(pub, "duration_days"):
        pub.duration_days = duration_days

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
        description=pub.description,
        status=pub.status,
        created_by_user_id=pub.created_by_user_id,
        created_at=pub.created_at.isoformat() if pub.created_at else "",
        photos=saved_urls,
        rating_avg=getattr(pub, "rating_avg", 0.0) or 0.0,
        rating_count=getattr(pub, "rating_count", 0) or 0,
        categories=slugs if slugs else [c.slug for c in getattr(pub, "categories", [])],
    )

@router.delete("/{pub_id}", status_code=status.HTTP_200_OK)
def delete_publication(
    pub_id: int, 
    payload: RejectRequest,
    db: Session = Depends(get_db), 
    _: models.User = Depends(require_admin)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    
    # Cambiar estado a "deleted" en lugar de eliminar físicamente
    pub.status = "deleted"
    pub.rejection_reason = payload.reason  # Reutilizamos este campo como deletion_reason
    db.commit()
    return {"message": "Publicación marcada como eliminada"}

# --- SUBMIT PUBLICATION (usuarios básicos) ---
@router.post("/submit", response_model=schemas.PublicationOut, status_code=status.HTTP_201_CREATED)
def submit_publication(
    place_name: str = Form(...),
    country: str = Form(...),
    province: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    description: str = Form(...),

    # mismos campos que en el backoffice
    categories: Optional[str] = Form(None),        # CSV: aventura,cultura
    continent: Optional[str] = Form(None),         # ej: europa / américa
    climate: Optional[str] = Form(None),           # ej: templado / tropical
    activities: Optional[str] = Form(None),        # CSV: playa,gastronomía
    cost_per_day: Optional[float] = Form(None),    # ej: 80.0
    duration_days: Optional[int] = Form(None),     # ej: 7

    photos: Optional[List[UploadFile]] = File(None),

    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # validar fotos
    files = photos or []
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Máximo 4 fotos por publicación")
    for f in files:
        if f.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Formato de imagen inválido (usa JPG/PNG/WebP)")

    # street/number legacy
    street, number = address, None
    parts = address.strip().rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        street, number = parts[0], parts[1]

    # normalizaciones
    continent_norm  = _norm_continent(continent)
    climate_norm    = _norm_climate(climate)
    activities_list = _csv_to_list(activities)

    # crear publicación PENDING
    pub = models.Publication(
        place_name=place_name,
        name=place_name,
        country=country,
        province=province,
        city=city,
        address=address,
        street=street,
        description=description,
        status="pending",
        created_by_user_id=current_user.id,
        created_at=datetime.now(timezone.utc),

        # mismos campos que backoffice (si existen en el modelo)
        continent=continent_norm if hasattr(models.Publication, "continent") else None,
        climate=climate_norm if hasattr(models.Publication, "climate") else None,
        activities=activities_list if hasattr(models.Publication, "activities") else None,
        cost_per_day=cost_per_day if hasattr(models.Publication, "cost_per_day") else None,
        duration_days=duration_days if hasattr(models.Publication, "duration_days") else None,
    )
    if hasattr(models.Publication, "number"):
        setattr(pub, "number", number)

    # categorías
    slugs: List[str] = []
    if categories:
        slugs = [_normalize_slug(s) for s in categories.split(",") if _normalize_slug(s)]
        for slug in slugs:
            cat = _get_or_create_category(db, slug)
            if hasattr(pub, "categories"):
                pub.categories.append(cat)

    db.add(pub)
    db.flush()

    # guardar fotos
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
        status=pub.status,
        description=pub.description,
        created_by_user_id=pub.created_by_user_id,
        created_at=pub.created_at.isoformat() if pub.created_at else "",
        photos=saved_urls,
        # si tu schema incluye estos campos, se completan
        **({"rating_avg": getattr(pub, "rating_avg", 0.0) or 0.0} if hasattr(schemas.PublicationOut, "model_fields") or hasattr(schemas.PublicationOut, "__fields__") else {}),
    )

# --- GET MY SUBMISSIONS (usuarios ven sus propias publicaciones) ---
@router.get("/my-submissions", response_model=List[schemas.PublicationOut])
def list_my_submissions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    pubs = db.query(models.Publication).filter(
        models.Publication.created_by_user_id == current_user.id
    ).order_by(models.Publication.created_at.desc()).all()

    # Obtener IDs de publicaciones con solicitud de eliminación pendiente
    pending_deletion_ids = {
        req.publication_id
        for req in db.query(models.DeletionRequest).filter(
            models.DeletionRequest.status == "pending"
        ).all()
    }

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
                status=p.status,
                rejection_reason=getattr(p, "rejection_reason", None),
                created_by_user_id=p.created_by_user_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                has_pending_deletion=p.id in pending_deletion_ids,
            )
        )
    return out

# --- SEARCH PUBLICATIONS ---
@router.get("/search", response_model=List[schemas.PublicationOut])
def search_publications(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Busca publicaciones aprobadas por: país, provincia, ciudad, lugar o dirección
    """
    if not q or len(q.strip()) < 2:
        # Si no hay búsqueda o es muy corta, devolver todas las aprobadas
        pubs = db.query(models.Publication).filter(
            models.Publication.status == "approved"
        ).order_by(models.Publication.created_at.desc()).all()
    else:
        search_term = f"%{q.lower()}%"
        pubs = db.query(models.Publication).filter(
            models.Publication.status == "approved",
            (
                models.Publication.place_name.ilike(search_term) |
                models.Publication.country.ilike(search_term) |
                models.Publication.province.ilike(search_term) |
                models.Publication.city.ilike(search_term) |
                models.Publication.address.ilike(search_term)
            )
        ).order_by(models.Publication.created_at.desc()).all()

    # Obtener IDs de favoritos del usuario actual
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()
    }

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
                status=p.status,
                created_by_user_id=p.created_by_user_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                is_favorite=p.id in favorite_ids,
            )
        )
    return out

# --- LIST PUBLIC (con auth opcional, con filtro de categorías) ---
def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Obtiene el usuario si está autenticado, sino devuelve None"""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        from ..security import decode_token
        token = authorization.split()[1]
        data = decode_token(token)
        if not data:
            return None
        user_id = data.get("sub")
        if user_id is None:
            return None
        user = db.query(models.User).get(int(user_id))
        return user
    except Exception:
        return None

@router.get("/public", response_model=List[schemas.PublicationOut])
def list_publications_public(
    category: Optional[str] = Query(None, description="Slugs separados por coma, ej: aventura,cultura"),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    """
    Lista publicaciones aprobadas. Permite filtrar por una o varias categorías usando slugs.
    No requiere autenticación, pero si el usuario está autenticado, incluye is_favorite.
    """
    q = db.query(models.Publication).filter(models.Publication.status == "approved")
    slugs: List[str] = []
    if category:
        slugs = [_normalize_slug(s) for s in category.split(",") if _normalize_slug(s)]
        if slugs:
            # join por la relación para evitar referenciar la tabla intermedia directamente
            q = q.join(models.Publication.categories).filter(models.Category.slug.in_(slugs)).distinct()

    pubs = q.order_by(models.Publication.created_at.desc()).all()
    
    # Obtener IDs de favoritos del usuario actual si está autenticado
    favorite_ids = set()
    if current_user:
        favorite_ids = {
            fav.publication_id
            for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()
        }
    
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
                status=p.status,
                created_by_user_id=p.created_by_user_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                rating_avg=getattr(p, "rating_avg", 0.0) or 0.0,
                rating_count=getattr(p, "rating_count", 0) or 0,
                categories=[c.slug for c in getattr(p, "categories", [])],
                is_favorite=p.id in favorite_ids,
                description=getattr(p, "description", None),

                continent=getattr(p, "continent", None),
                climate=getattr(p, "climate", None),
                activities=getattr(p, "activities", []),
                cost_per_day=getattr(p, "cost_per_day", None),
                duration_days=getattr(p, "duration_days", None),
            )
        )
    return out

# --- GET PENDING PUBLICATIONS (solo admin) ---
@router.get("/pending", response_model=List[schemas.PublicationOut])
def list_pending_publications(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pubs = (
        db.query(models.Publication)
        .filter(models.Publication.status == "pending")
        .order_by(models.Publication.created_at.desc())
        .all()
    )
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
                status=p.status,
                created_by_user_id=p.created_by_user_id,
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
    user: models.User = Depends(require_premium), # <-- premium requerido
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

@router.get("/{pub_id}/reviews", response_model=List[schemas.ReviewOut])
def list_reviews(pub_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Review, models.User.username)
        .join(models.User, models.User.id == models.Review.author_id)
        .filter(models.Review.publication_id == pub_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
    out: List[schemas.ReviewOut] = []
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

# --- APPROVE PUBLICATION (solo admin) ---
@router.put("/{pub_id}/approve", response_model=schemas.PublicationOut)
def approve_publication(pub_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    pub.status = "approved"
    db.commit()
    db.refresh(pub)

    return schemas.PublicationOut(
        id=pub.id,
        place_name=pub.place_name,
        country=pub.country,
        province=pub.province,
        city=pub.city,
        address=pub.address,
        status=pub.status,
        created_by_user_id=pub.created_by_user_id,
        created_at=pub.created_at.isoformat() if pub.created_at else "",
        photos=[ph.url for ph in pub.photos],
    )

# --- REJECT PUBLICATION (solo admin) - Cambia status a "rejected" ---
class RejectRequest(BaseModel):
    reason: Optional[str] = None

@router.put("/{pub_id}/reject", response_model=schemas.PublicationOut)
def reject_publication(
    pub_id: int, 
    payload: RejectRequest,
    db: Session = Depends(get_db), 
    _: models.User = Depends(require_admin)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    pub.status = "rejected"
    pub.rejection_reason = payload.reason
    db.commit()
    db.refresh(pub)

    return schemas.PublicationOut(
        id=pub.id,
        place_name=pub.place_name,
        country=pub.country,
        province=pub.province,
        city=pub.city,
        address=pub.address,
        status=pub.status,
        rejection_reason=pub.rejection_reason,
        created_by_user_id=pub.created_by_user_id,
        created_at=pub.created_at.isoformat() if pub.created_at else "",
        photos=[ph.url for ph in pub.photos],
    )

# --- TOGGLE FAVORITE ---
@router.post("/{pub_id}/favorite", status_code=status.HTTP_200_OK)
def toggle_favorite(pub_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Agrega o quita una publicación de favoritos
    """
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    # Verificar si ya existe el favorito
    existing_fav = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.publication_id == pub_id
    ).first()

    if existing_fav:
        # Si existe, lo eliminamos (unfavorite)
        db.delete(existing_fav)
        db.commit()
        return {"message": "Eliminado de favoritos", "is_favorite": False}
    else:
        # Si no existe, lo agregamos
        new_fav = models.Favorite(user_id=current_user.id, publication_id=pub_id)
        db.add(new_fav)
        db.commit()
        return {"message": "Agregado a favoritos", "is_favorite": True}

# --- GET MY FAVORITES ---
@router.get("/favorites", response_model=List[schemas.PublicationOut])
def list_my_favorites(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Devuelve todas las publicaciones favoritas del usuario actual
    """
    favorites = (
        db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.id)
        .order_by(models.Favorite.created_at.desc())
        .all()
    )

    out: List[schemas.PublicationOut] = []
    for fav in favorites:
        p = fav.publication
        if p and p.status == "approved":  # Solo mostrar si está aprobada
            out.append(
                schemas.PublicationOut(
                    id=p.id,
                    place_name=p.place_name,
                    country=p.country,
                    province=p.province,
                    city=p.city,
                    address=p.address,
                    status=p.status,
                    created_by_user_id=p.created_by_user_id,
                    created_at=p.created_at.isoformat() if p.created_at else "",
                    photos=[ph.url for ph in p.photos],
                    is_favorite=True,
                    favorite_status=fav.status,
                )
            )
    return out

# --- REQUEST DELETION (usuarios básicos) ---
@router.post("/{pub_id}/request-deletion", status_code=status.HTTP_200_OK)
def request_deletion(pub_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Un usuario solicita eliminar una publicación (debe ser aprobada por admin)
    """
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    # Verificar si ya existe una solicitud pendiente
    existing_request = db.query(models.DeletionRequest).filter(
        models.DeletionRequest.publication_id == pub_id,
        models.DeletionRequest.status == "pending"
    ).first()

    if existing_request:
        raise HTTPException(status_code=400, detail="Ya existe una solicitud de eliminación pendiente para esta publicación")

    # Crear nueva solicitud
    new_request = models.DeletionRequest(
        publication_id=pub_id,
        requested_by_user_id=current_user.id
    )
    db.add(new_request)
    db.commit()

    return {"message": "Solicitud de eliminación enviada. Será revisada por un administrador."}

# --- GET PENDING DELETION REQUESTS (solo admin) ---
@router.get("/deletion-requests/pending", response_model=List[schemas.DeletionRequestOut])
def list_pending_deletion_requests(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    """
    Lista todas las solicitudes de eliminación pendientes
    """
    requests = (
        db.query(models.DeletionRequest)
        .filter(models.DeletionRequest.status == "pending")
        .order_by(models.DeletionRequest.created_at.desc())
        .all()
    )

    out: List[schemas.DeletionRequestOut] = []
    for req in requests:
        p = req.publication
        if p:
            pub_out = schemas.PublicationOut(
                id=p.id,
                place_name=p.place_name,
                country=p.country,
                province=p.province,
                city=p.city,
                address=p.address,
                status=p.status,
                created_by_user_id=p.created_by_user_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                photos=[ph.url for ph in p.photos],
                is_favorite=False,
                has_pending_deletion=True
            )

            out.append(
                schemas.DeletionRequestOut(
                    id=req.id,
                    publication_id=req.publication_id,
                    requested_by_user_id=req.requested_by_user_id,
                    status=req.status,
                    rejection_reason=getattr(req, "rejection_reason", None),
                    created_at=req.created_at.isoformat() if req.created_at else "",
                    publication=pub_out
                )
            )
    return out

# --- APPROVE DELETION REQUEST (solo admin) ---
@router.put("/deletion-requests/{request_id}/approve", status_code=status.HTTP_200_OK)
def approve_deletion_request(request_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    """
    Aprueba la solicitud de eliminación y elimina la publicación
    """
    req = db.query(models.DeletionRequest).filter(models.DeletionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Esta solicitud ya fue procesada")

    # Obtener la publicación
    pub = req.publication
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    # Borrar archivos físicos
    for ph in pub.photos:
        filename = ph.url.split("/static/uploads/publications/")[-1]
        abs_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception:
            pass

    # Eliminar la publicación (cascada eliminará fotos y solicitud)
    db.delete(pub)

    # Actualizar estado de la solicitud
    req.status = "approved"
    req.resolved_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Solicitud aprobada. Publicación eliminada."}

# --- REJECT DELETION REQUEST (solo admin) ---
@router.put("/deletion-requests/{request_id}/reject", status_code=status.HTTP_200_OK)
def reject_deletion_request(
    request_id: int, 
    payload: RejectRequest,
    db: Session = Depends(get_db), 
    _: models.User = Depends(require_admin)
):
    """
    Rechaza la solicitud de eliminación
    """
    req = db.query(models.DeletionRequest).filter(models.DeletionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Esta solicitud ya fue procesada")

    req.status = "rejected"
    req.rejection_reason = payload.reason
    req.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Solicitud de eliminación rechazada."}


class FavoriteStatusUpdate(BaseModel):
    status: str  # "pending" o "done"

@router.put("/favorites/{pub_id}/status", status_code=status.HTTP_200_OK)
def update_favorite_status(
    pub_id: int,
    payload: FavoriteStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Actualiza el estado de un favorito (pending/done)
    """
    fav = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.publication_id == pub_id
    ).first()

    if not fav:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")

    if payload.status not in ("pending", "done"):
        raise HTTPException(status_code=400, detail="Estado inválido")

    fav.status = payload.status
    db.commit()
    return {"message": f"Estado actualizado a {payload.status}"}