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
from sqlalchemy.orm import Session, selectinload
import shutil
import uuid
import os
import json
from json import JSONDecodeError
from ..utils.match import compute_match_percentage
from collections.abc import Sequence  
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

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

    def extract_pref_keywords(pref) -> list[str]:
        """
        Devuelve una lista de strings con las preferencias del usuario.
        Soporta tanto:
           - pref = objeto UserPreference
           - pref = lista (InstrumentedList) de UserPreference
        """
        if not pref:
            return []

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

    my_keywords = extract_pref_keywords(getattr(current_user, "preference", None))

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

        other_keywords = extract_pref_keywords(getattr(u, "preference", None))

        match_percentage = compute_match_percentage(
            me_keywords=my_keywords,
            other_keywords=other_keywords,
        ) or 0

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

@router.get("/points")
def get_user_points(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los puntos actuales del usuario."""
    user_points = db.query(models.UserPoints).filter(
        models.UserPoints.user_id == current_user.id
    ).first()
    
    return {
        "points": user_points.total_points if user_points else 0
    }


@router.get("/points/movements")
def get_points_movements(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el historial de movimientos de puntos del usuario."""
    movements = db.query(models.PointsTransaction).filter(
        models.PointsTransaction.user_id == current_user.id
    ).order_by(models.PointsTransaction.created_at.desc()).all()
    
    return movements


@router.get("/benefits")
def get_premium_benefits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los beneficios premium disponibles."""
    if current_user.role != "premium":
        raise HTTPException(
            status_code=403,
            detail="Función disponible solo para usuarios premium."
        )
    
    benefits = db.query(models.PremiumBenefit).filter(
        models.PremiumBenefit.is_active == True
    ).join(models.Publication).options(
        selectinload(models.PremiumBenefit.publication).selectinload(models.Publication.photos),
        selectinload(models.PremiumBenefit.publication).selectinload(models.Publication.categories)
    ).all()
    
    result = []
    for benefit in benefits:
        pub = benefit.publication
        result.append({
            "id": benefit.id,
            "title": benefit.title,
            "description": benefit.description,
            "discount_percentage": benefit.discount_percentage,
            "benefit_type": benefit.benefit_type,
            "terms_conditions": benefit.terms_conditions,
            "publication": {
                "id": pub.id,
                "place_name": pub.place_name,
                "country": pub.country,
                "province": pub.province,
                "city": pub.city,
                "address": pub.address,
                "description": pub.description,
                "status": pub.status,
                "created_at": pub.created_at.isoformat() if pub.created_at else "",
                "photos": [ph.url for ph in pub.photos],
                "rating_avg": getattr(pub, "rating_avg", 0.0) or 0.0,
                "rating_count": getattr(pub, "rating_count", 0) or 0,
                "categories": [c.slug for c in getattr(pub, "categories", [])],
                "continent": getattr(pub, "continent", None),
                "climate": getattr(pub, "climate", None),
                "activities": getattr(pub, "activities", []),
                "cost_per_day": getattr(pub, "cost_per_day", None),
                "duration_min": getattr(pub, "duration_min", None),
                "is_favorite": False
            }
        })
    
    return result


@router.post("/benefits/{benefit_id}/redeem")
def redeem_benefit(
    benefit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Canjear un beneficio premium por puntos."""
    if current_user.role != "premium":
        raise HTTPException(
            status_code=403,
            detail="Función disponible solo para usuarios premium."
        )
    
    benefit = db.query(models.PremiumBenefit).filter(
        models.PremiumBenefit.id == benefit_id,
        models.PremiumBenefit.is_active == True
    ).first()
    
    if not benefit:
        raise HTTPException(status_code=404, detail="Beneficio no encontrado")
    
    existing = db.query(models.UserBenefit).filter(
        models.UserBenefit.user_id == current_user.id,
        models.UserBenefit.benefit_id == benefit_id,
        models.UserBenefit.is_used == False
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya tienes este beneficio disponible")
    
    if benefit.discount_percentage:
        points_cost = benefit.discount_percentage * 2
    else:
        points_cost = 20
    
    user_points = db.query(models.UserPoints).filter(
        models.UserPoints.user_id == current_user.id
    ).first()
    
    if not user_points or user_points.total_points < points_cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Puntos insuficientes. Necesitas {points_cost} puntos, tienes {user_points.total_points if user_points else 0}"
        )
    
    import uuid
    voucher_code = f"PG{str(uuid.uuid4()).replace('-', '')[:10].upper()}"
    
    user_benefit = models.UserBenefit(
        user_id=current_user.id,
        benefit_id=benefit_id,
        points_cost=points_cost,
        voucher_code=voucher_code,
        is_used=False
    )
    db.add(user_benefit)
    
    user_points.total_points -= points_cost
    
    transaction = models.PointsTransaction(
        user_id=current_user.id,
        points=-points_cost,
        transaction_type="redeemed",
        description=f"Beneficio: {benefit.title}"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(user_benefit)
    
    return {
        "success": True,
        "message": "Beneficio obtenido exitosamente",
        "voucher_code": voucher_code,
        "points_used": points_cost,
        "remaining_points": user_points.total_points
    }


@router.get("/my-benefits")
def get_user_benefits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los beneficios que el usuario ha canjeado."""
    if current_user.role != "premium":
        raise HTTPException(
            status_code=403,
            detail="Función disponible solo para usuarios premium."
        )
    
    user_benefits = db.query(models.UserBenefit).filter(
        models.UserBenefit.user_id == current_user.id,
        models.UserBenefit.is_used == False
    ).join(models.PremiumBenefit).join(models.Publication).all()
    
    result = []
    for user_benefit in user_benefits:
        benefit = user_benefit.benefit
        publication = benefit.publication
        
        original_price = publication.cost_per_day
        discounted_price = None
        if original_price and benefit.discount_percentage:
            discounted_price = original_price * (1 - benefit.discount_percentage / 100)
        
        result.append({
            "id": user_benefit.id,
            "voucher_code": user_benefit.voucher_code,
            "obtained_at": user_benefit.obtained_at.isoformat(),
            "points_cost": user_benefit.points_cost,
            "benefit": {
                "title": benefit.title,
                "description": benefit.description,
                "discount_percentage": benefit.discount_percentage,
                "benefit_type": benefit.benefit_type,
                "terms_conditions": benefit.terms_conditions,
                "publication": {
                    "id": publication.id,
                    "place_name": publication.place_name,
                    "city": publication.city,
                    "province": publication.province,
                    "address": publication.address,
                    "original_price": original_price,
                    "discounted_price": discounted_price
                }
            }
        })
    
    return result


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


