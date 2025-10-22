from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import os
import re
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

_STREET_NUM_RE = re.compile(r"\s*(.+?)\s+(\d+[A-Za-z\-]*)\s*$")
def split_street_number(address: str) -> tuple[str, str]:
    m = _STREET_NUM_RE.match(address or "")
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # fallback si no se puede parsear: “s/n” = sin número
    return (address or "").strip(), "s/n"

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

    # dividir address en street/number (legacy), si se puede
    street, number = address, None
    parts = address.strip().rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        street, number = parts[0], parts[1]

    # crear publicación (seteamos created_at por legacy NOT NULL)
    pub = models.Publication(
        place_name=place_name,
        name=place_name,                     # compat con columna legacy 'name'
        country=country,
        province=province,
        city=city,
        address=address,
        street=street,                       # compat con columna legacy 'street'
        created_at=datetime.now(timezone.utc)
    )
    if hasattr(models.Publication, "number"):
        setattr(pub, "number", number)

    db.add(pub)
    db.flush()  # necesitamos pub.id para asociar fotos

    # guardar archivos
    saved_urls: List[str] = []
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
        # importante: index_order para la tabla legacy NOT NULL
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
    )

# --- DELETE ---
@router.delete("/{pub_id}", status_code=status.HTTP_200_OK)
def delete_publication(pub_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    # borrar archivos físicos
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
