# backend/app/api/users.py
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    Query,
    Request
)
from sqlalchemy.orm import Session
import shutil
import uuid
import os
import json
from json import JSONDecodeError
from ..utils.match import compute_match_percentage  # 👈 nuevo import
from collections.abc import Sequence  
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


@router.get("/travelers", response_model=list[schemas.TravelerCardOut])
def list_travelers(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Lista viajeros (otros usuarios) y calcula el % de coincidencia
    en base a las preferencias configuradas (UserPreference).
    """

    # --- helper: saca TODAS las preferencias (climas+actividades+continentes) ---
    def extract_pref_keywords(pref) -> list[str]:
        """
        Devuelve una lista de strings con las preferencias del usuario.
        Soporta tanto:
           - pref = objeto UserPreference
           - pref = lista (InstrumentedList) de UserPreference
        """
        if not pref:
            return []

        # Si viene como lista / InstrumentedList, usamos el primero (relación 1-1)
        if isinstance(pref, Sequence) and not isinstance(pref, (str, bytes)):
            if not pref:
                return []
            pref = pref[0]

        keywords: list[str] = []

        for field in ("climates", "activities", "continents"):
            arr = getattr(pref, field, None)
            if isinstance(arr, list):
                keywords.extend(arr)

        return keywords

    # preferencias del usuario logueado (A)
    my_keywords = extract_pref_keywords(getattr(current_user, "preference", None))

    # (usamos q solo para filtrar por nombre/username, el resto lo hace el front)
    q = request.query_params.get("q") or None

    query = db.query(models.User).filter(models.User.id != current_user.id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.User.username.ilike(like))
            | (models.User.first_name.ilike(like))
            | (models.User.last_name.ilike(like))
        )

    users = query.all()
    travelers: list[schemas.TravelerCardOut] = []

    for u in users:
        # travel_profile para mostrar la card (destinos, estilo, etc.)
        try:
            prefs_json = json.loads(u.travel_preferences) if u.travel_preferences else {}
        except (JSONDecodeError, TypeError):
            prefs_json = {}

        destinations = prefs_json.get("destinations", []) or []
        style = prefs_json.get("style", "") or ""
        budget = prefs_json.get("budget", "") or ""
        about = prefs_json.get("about", "") or ""
        tags = prefs_json.get("tags", []) or []
        city = prefs_json.get("city", "") or ""

        # preferencias del usuario de la tarjeta (B)
        other_keywords = extract_pref_keywords(getattr(u, "preference", None))

        # --- cálculo de coincidencia con la función utilitaria ---
        match_percentage = compute_match_percentage(
            me_keywords=my_keywords,
            other_keywords=other_keywords,
        ) or 0  # por si algún día devolvés None

        travelers.append(
            schemas.TravelerCardOut(
                id=u.id,
                username=u.username,
                name=u.first_name or u.username,
                city=city,
                destinations=destinations,
                style=style,
                budget=budget,
                about=about,
                tags=tags,
                matches_with_you=match_percentage,
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


