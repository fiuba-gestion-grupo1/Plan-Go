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
    # Solo mostrar publicaciones APROBADAS en la lista principal
    pubs = db.query(models.Publication).filter(models.Publication.status == "approved").order_by(models.Publication.created_at.desc()).all()
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
    current_user: models.User = Depends(require_admin),
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
        status="approved",                   # por defecto aprobado cuando lo crea un admin
        created_by_user_id=current_user.id,  # registrar quién lo creó
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
        status=pub.status,
        created_by_user_id=pub.created_by_user_id,
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

# --- SUBMIT PUBLICATION (usuarios básicos) ---
@router.post("/submit", response_model=schemas.PublicationOut, status_code=status.HTTP_201_CREATED)
def submit_publication(
    place_name: str = Form(...),
    country: str = Form(...),
    province: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
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

    # dividir address en street/number (legacy), si se puede
    street, number = address, None
    parts = address.strip().rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        street, number = parts[0], parts[1]

    # crear publicación con status PENDING (esperando aprobación)
    pub = models.Publication(
        place_name=place_name,
        name=place_name,
        country=country,
        province=province,
        city=city,
        address=address,
        street=street,
        status="pending",  # 🔹 pendiente de aprobación
        created_by_user_id=current_user.id,
        created_at=datetime.now(timezone.utc)
    )
    if hasattr(models.Publication, "number"):
        setattr(pub, "number", number)

    db.add(pub)
    db.flush()

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
        created_by_user_id=pub.created_by_user_id,
        created_at=pub.created_at.isoformat() if pub.created_at else "",
        photos=saved_urls,
    )

# --- GET MY SUBMISSIONS (usuarios ven sus propias publicaciones) ---
@router.get("/my-submissions", response_model=List[schemas.PublicationOut])
def list_my_submissions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    pubs = db.query(models.Publication).filter(
        models.Publication.created_by_user_id == current_user.id
    ).order_by(models.Publication.created_at.desc()).all()
    
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
            )
        )
    return out

# --- SEARCH PUBLICATIONS ---
@router.get("/search", response_model=List[schemas.PublicationOut])
def search_publications(q: str = "", db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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
    favorite_ids = {fav.publication_id for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()}
    
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

# --- GET PUBLICATION FOR USERS ---
@router.get("/public", response_model=List[schemas.PublicationOut])
def list_publications_public(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Solo mostrar publicaciones APROBADAS
    pubs = db.query(models.Publication).filter(models.Publication.status == "approved").order_by(models.Publication.created_at.desc()).all()
    
    # Obtener IDs de favoritos del usuario actual
    favorite_ids = {fav.publication_id for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()}
    
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

# --- GET PENDING PUBLICATIONS (solo admin) ---
@router.get("/pending", response_model=List[schemas.PublicationOut])
def list_pending_publications(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pubs = db.query(models.Publication).filter(models.Publication.status == "pending").order_by(models.Publication.created_at.desc()).all()
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
@router.put("/{pub_id}/reject", response_model=schemas.PublicationOut)
def reject_publication(pub_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    
    pub.status = "rejected"
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
    favorites = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id
    ).order_by(models.Favorite.created_at.desc()).all()
    
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
                )
            )
    return out
