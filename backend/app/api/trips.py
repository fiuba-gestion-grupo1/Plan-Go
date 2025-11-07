from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .auth import get_current_user
from .. import models
from fastapi.responses import FileResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

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

@router.get("/{trip_id}/expenses/export", response_class=FileResponse)
def export_trip_expenses(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id, user_id=user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    expenses = db.query(models.Expense).filter_by(trip_id=trip_id).all()
    if not expenses:
        raise HTTPException(status_code=404, detail="No hay gastos registrados")

    # Crear archivo temporal
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmpfile.name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    elements.append(Paragraph(f"Gastos del viaje: {trip.name}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Tabla
    data = [["Fecha", "Nombre", "Categoría", "Monto ($)"]]
    total = 0
    for e in expenses:
        data.append([e.date.strftime("%d/%m/%Y"), e.name, e.category, f"{e.amount:.2f}"])
        total += e.amount

    data.append(["", "", "TOTAL", f"${total:.2f}"])

    table = Table(data, colWidths=[80, 160, 120, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3A92B5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    elements.append(table)
    doc.build(elements)

    return FileResponse(tmpfile.name, filename=f"Gastos_{trip.name}.pdf", media_type="application/pdf")



# --- Agregar participante premium ---
@router.post("/{trip_id}/participants")
def join_trip(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    if user.role != "premium":
        raise HTTPException(status_code=403, detail="Solo los usuarios premium pueden unirse a un viaje")

    existing = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya sos participante de este viaje")

    participant = models.TripParticipant(trip_id=trip_id, user_id=user.id)
    db.add(participant)
    db.commit()
    return {"message": f"Te uniste al viaje '{trip.name}'"}


# --- Calcular saldos ---
@router.get("/{trip_id}/balances")
def calculate_balances(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    expenses = db.query(models.Expense).filter_by(trip_id=trip_id).all()
    if not expenses:
        return {"total": 0, "balances": []}

    total = sum(e.amount for e in expenses)
    participants = db.query(models.TripParticipant).filter_by(trip_id=trip_id).all()
    if not participants:
        raise HTTPException(status_code=400, detail="No hay participantes en este viaje")

    share = round(total / len(participants), 2)
    balances = [{"user_id": p.user_id, "debe": share} for p in participants]

    return {"total": total, "por_persona": share, "balances": balances}