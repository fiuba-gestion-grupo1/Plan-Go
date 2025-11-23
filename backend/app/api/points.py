from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from ..db import get_db
from ..schemas import UserPointsOut, PointsTransactionOut, AddPointsRequest
from ..models import User, UserPoints, PointsTransaction
from .auth import get_current_user

router = APIRouter()

def get_or_create_user_points(db: Session, user_id: int) -> UserPoints:
    """Obtiene o crea el registro de puntos para un usuario"""
    user_points = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if not user_points:
        user_points = UserPoints(user_id=user_id, total_points=0)
        db.add(user_points)
        db.commit()
        db.refresh(user_points)
    return user_points


@router.get("/points", response_model=dict)
async def get_user_points(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los puntos actuales del usuario"""
    user_points = get_or_create_user_points(db, current_user.id)
    return {
        "user_id": current_user.id,
        "points": user_points.total_points,
        "updated_at": user_points.updated_at.isoformat()
    }


@router.get("/points/movements", response_model=List[PointsTransactionOut])
async def get_points_movements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el historial de movimientos de puntos del usuario"""
    transactions = db.query(PointsTransaction)\
        .filter(PointsTransaction.user_id == current_user.id)\
        .order_by(desc(PointsTransaction.created_at))\
        .limit(100)\
        .all()
    
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "points": t.points,
            "transaction_type": t.transaction_type,
            "description": t.description,
            "reference_id": t.reference_id,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions
    ]


@router.post("/points/add")
async def add_points(
    request: AddPointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Agrega puntos a un usuario (solo para uso interno del sistema)
    En producción, esto debería estar protegido y solo ser llamado por otros endpoints
    """
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    user_points = get_or_create_user_points(db, request.user_id)

    transaction = PointsTransaction(
        user_id=request.user_id,
        points=request.points,
        transaction_type=request.transaction_type,
        description=request.description,
        reference_id=request.reference_id
    )
    db.add(transaction)

    user_points.total_points += request.points
    
    if user_points.total_points < 0:
        user_points.total_points = 0

    db.commit()
    db.refresh(transaction)

    return {
        "message": "Puntos agregados exitosamente",
        "transaction_id": transaction.id,
        "new_balance": user_points.total_points
    }


def award_points_for_review(db: Session, user_id: int, review_id: int, points: int = 10):
    """
    Función helper para otorgar puntos por escribir una reseña
    Debe ser llamada cuando se crea una nueva reseña
    """

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != 'premium':
        return False

    existing = db.query(PointsTransaction).filter(
        PointsTransaction.user_id == user_id,
        PointsTransaction.transaction_type == 'review_earned',
        PointsTransaction.reference_id == review_id
    ).first()
    
    if existing:
        return False

    from ..models import Review, Publication
    review = db.query(Review).filter(Review.id == review_id).first()
    publication_name = "Publicación desconocida"
    
    if review and review.publication:
        publication_name = review.publication.place_name or review.publication.name or f"Publicación #{review.publication.id}"
    
    transaction = PointsTransaction(
        user_id=user_id,
        points=points,
        transaction_type='review_earned',
        description=f"Puntos ganados por escribir reseña de '{publication_name}'",
        reference_id=review_id
    )
    db.add(transaction)

    user_points = get_or_create_user_points(db, user_id)
    user_points.total_points += points

    db.commit()
    return True