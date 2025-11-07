from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .auth import get_current_user
from .. import models

router = APIRouter(prefix="/api/trips", tags=["trips"])

@router.get("")
def get_my_trips(db: Session = Depends(get_db), user=Depends(get_current_user)):
    trips = db.query(models.Trip).filter_by(user_id=user.id).all()
    return [{"id": t.id, "name": t.name, "created_at": t.created_at} for t in trips]

@router.post("")
def create_trip(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="El nombre del viaje es obligatorio")
    trip = models.Trip(user_id=user.id, name=name)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return {"id": trip.id, "name": trip.name}

@router.get("/{trip_id}/expenses")
def get_trip_expenses(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id, user_id=user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    return [
        {"id": e.id, "name": e.name, "category": e.category, "amount": e.amount, "date": e.date}
        for e in trip.expenses
    ]

from datetime import datetime

@router.post("/{trip_id}/expenses")
def add_expense(trip_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id, user_id=user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")


    try:
        date_obj = datetime.strptime(payload.get("date"), "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (use YYYY-MM-DD)")

    exp = models.Expense(
        trip_id=trip.id,
        name=payload.get("name"),
        category=payload.get("category"),
        amount=payload.get("amount"),
        date=date_obj, 
    )

    db.add(exp)
    db.commit()
    db.refresh(exp)

    return {
        "id": exp.id,
        "name": exp.name,
        "category": exp.category,
        "amount": exp.amount,
        "date": str(exp.date),
    }

