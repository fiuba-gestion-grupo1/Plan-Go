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

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not (current_user.role == "admin" or current_user.username == "admin"):
        raise HTTPException(status_code=403, detail="Solo administradores")
    return current_user

def require_premium_or_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    # Si QUERÉS que solo premium (sin admin) puedan reseñar, cambiá la línea de abajo por:  if current_user.role != "premium":
    if current_user.role not in ("premium", "admin"):
        raise HTTPException(status_code=403, detail="Solo usuarios premium pueden publicar reseñas")
    return current_user



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
                rating_avg=p.rating_avg or 0.0,
                rating_count=p.rating_count or 0,
                categories=[c.slug for c in p.categories],
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

    pub = models.Publication(
        place_name=place_name,
        name=place_name,
        country=country,
        province=province,
        city=city,
        address=address,
        street=street,
        created_at=datetime.now(timezone.utc),
    )
    if hasattr(models.Publication, "number"):
        setattr(pub, "number", number)

    # categorías (opc)
    slugs: List[str] = []
    if categories:
        slugs = [_normalize_slug(s) for s in categories.split(",") if _normalize_slug(s)]
        for slug in slugs:
            cat = _get_or_create_category(db, slug)
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
        rating_avg=pub.rating_avg or 0.0,
        rating_count=pub.rating_count or 0,
        categories=slugs if slugs else [c.slug for c in pub.categories],
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
            q = (q.join(models.publication_categories)
                   .join(models.Category)
                   .filter(models.Category.slug.in_(slugs))
                   .distinct())
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
                rating_avg=p.rating_avg or 0.0,
                rating_count=p.rating_count or 0,
                categories=[c.slug for c in p.categories],
            )
        )
    return out

def _update_publication_rating(db: Session, pub_id: int) -> None:
    avg_, count_ = db.query(func.avg(models.Review.rating), func.count(models.Review.id)) \
        .filter(models.Review.publication_id == pub_id).one()
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    pub.rating_avg = round(float(avg_ or 0.0), 1)
    pub.rating_count = int(count_ or 0)
    db.add(pub)


@router.post("/{pub_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(pub_id: int, payload: dict, db: Session = Depends(get_db), user: models.User = Depends(require_premium_or_admin)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    if not (1 <= payload.rating <= 5):
        raise HTTPException(status_code=400, detail="El rating debe estar entre 1 y 5")
    review = models.Review(publication_id=pub_id, author_id=user.id, rating=payload.rating, comment=(payload.comment or "").strip() or None)
    db.add(review)
    db.flush()
    _update_publication_rating(db, pub_id)
    db.commit()
    db.refresh(review)
    return schemas.ReviewOut(
        id=review.id, rating=review.rating, comment=review.comment,
        author_username=user.username,
        created_at=review.created_at.isoformat() if review.created_at else "",
    )

@router.get("/{pub_id}/reviews", response_model=List[schemas.ReviewOut])
def list_reviews(pub_id: int, db: Session = Depends(get_db)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    rows = (db.query(models.Review, models.User.username)
              .join(models.User, models.User.id == models.Review.author_id)
              .filter(models.Review.publication_id == pub_id)
              .order_by(models.Review.created_at.desc())
              .all())
    out: List[schemas.ReviewOut] = []
    for r, username in rows:
        out.append(
            schemas.ReviewOut(
                id=r.id, rating=r.rating, comment=r.comment,
                author_username=username,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
        )
    return out
