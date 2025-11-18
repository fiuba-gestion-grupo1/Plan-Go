# backend/app/api/users.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import shutil
import uuid
import os
import json
from json import JSONDecodeError

from ..db import get_db
from .. import models, schemas
from .auth import get_current_user  # Importamos la dependencia desde auth.py

router = APIRouter(prefix="/api/users", tags=["users"])

UPLOAD_DIR = "backend/app/static/uploads"


@router.put("/me/photo", response_model=schemas.UserOut)
def upload_profile_photo(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo inválido. Solo se permiten JPG y PNG.",
        )

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Nos aseguramos de que exista el directorio
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    relative_path = f"/static/uploads/{unique_filename}"
    user.profile_picture_url = relative_path
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/me/subscribe", response_model=schemas.UserOut)
def subscribe_to_premium(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Simula un pago y actualiza el rol del usuario a 'premium'.
    """
    if user.role == "premium":
        raise HTTPException(status_code=400, detail="Ya eres usuario premium.")

    user.role = "premium"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/cancel-subscription", response_model=schemas.UserOut)
def cancel_subscription(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancela la suscripción y revierte el rol del usuario a 'user'.
    """
    if user.role != "premium":
        raise HTTPException(
            status_code=400, detail="No tienes una suscripción premium activa."
        )

    user.role = "user"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -----------------------------
# NUEVO: listar viajeros
# -----------------------------
@router.get("/travelers", response_model=list[schemas.TravelerCardOut])
def list_travelers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    users = db.query(models.User).filter(models.User.id != current_user.id).all()
    travelers = []

    for u in users:
        try:
            prefs = json.loads(u.travel_preferences) if u.travel_preferences else {}
        except (JSONDecodeError, TypeError):
            prefs = {}

        travelers.append(
            schemas.TravelerCardOut(
                id=u.id,
                username=u.username,
                name=u.first_name or u.username,
                city=prefs.get("city", ""),
                destinations=prefs.get("destinations", []),
                style=prefs.get("style", ""),
                budget=prefs.get("budget", ""),
                about=prefs.get("about", ""),
                tags=prefs.get("tags", []),
                matches_with_you=prefs.get("match_percentage", 0),
            )
        )

    return travelers


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Devuelve la info básica de un usuario (para encabezado de perfil viajero).
    """
    user = db.query(models.User).get(int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user