from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from .. import models, schemas
from ..db import get_db
from .auth import get_current_user  # ya existe
from fastapi import status

router = APIRouter(prefix="/api/publications", tags=["publications"])

# --- helper admin ---
def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not (current_user.role == "admin" or current_user.username == "admin"):
        raise HTTPException(status_code=403, detail="Solo administradores")
    return current_user

# --- path para subir fotos ---
UPLOAD_DIR = os.path.join("backend", "app", "static", "uploads", "publications")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- LIST ---
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
            )
        )
    return out

# --- CREATE ---
@router.post("", response_model=schemas.PublicationOut, status_code=status.HTTP_201_CREATED)
def create_publication(
    place_name: str = Form(...),
    country: str = Form(...),
    province: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    photos: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    # validar fotos
    files = photos or []
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Máximo 4 fotos por publicación")
    for f in files:
        if f.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Formato de imagen inválido (usa JPG/PNG/WebP)")

    pub = models.Publication(
        place_name=place_name,
        name=place_name,          # compat con columna 'name'
        country=country,
        province=province,
        city=city,
        address=address,
        street=address,           # compat con columna 'street' NOT NULL
    )
    db.add(pub)
    db.flush()
    db.commit()
    db.refresh(pub)

    saved_urls: List[str] = []
    # guardar archivos
    for idx, f in enumerate(files):
        ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(f.content_type, ".bin")
        filename = f"pub_{pub.id}_{idx}{ext}"
        abs_path = os.path.join(UPLOAD_DIR, filename)
        with open(abs_path, "wb") as out:
            out.write(f.file.read())
        url = f"/static/uploads/publications/{filename}"
        db.add(models.PublicationPhoto(publication_id=pub.id, url=url))
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
    )

# --- DELETE ---
@router.delete("/{pub_id}", status_code=status.HTTP_200_OK)
def delete_publication(pub_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    # borrar archivos físicos
    for ph in pub.photos:
        # ph.url -> /static/uploads/publications/filename
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
