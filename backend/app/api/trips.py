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
from datetime import datetime

router = APIRouter(prefix="/api/trips", tags=["trips"])


# --- Obtener viajes del usuario ---
@router.get("")
def get_my_trips(db: Session = Depends(get_db), user=Depends(get_current_user)):
    trips = db.query(models.Trip).filter_by(user_id=user.id).all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "created_at": t.created_at,
            "participants_count": len(t.participants)
        }
        for t in trips
    ]

# --- Crear viaje (agrega automáticamente al creador como participante) ---
from datetime import datetime

@router.post("")
def create_trip(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    name = payload.get("name")
    start = payload.get("start_date")
    end = payload.get("end_date")

    if not name:
        raise HTTPException(status_code=400, detail="El nombre del viaje es obligatorio")

    # ✅ Convert strings to date objects
    start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
    end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None

    trip = models.Trip(
        user_id=user.id,
        name=name,
        start_date=start_date,
        end_date=end_date,
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    db.add(models.TripParticipant(trip_id=trip.id, user_id=user.id))
    db.commit()

    return {
        "id": trip.id,
        "name": trip.name,
        "start_date": trip.start_date,
        "end_date": trip.end_date
    }

# --- Obtener gastos de un viaje ---
@router.get("/{trip_id}/expenses")
def get_trip_expenses(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id, user_id=user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    return [
        {"id": e.id, "name": e.name, "category": e.category, "amount": e.amount, "date": e.date}
        for e in trip.expenses
    ]


# --- Agregar gasto ---
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
        user_id=user.id,  
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

@router.delete("/{trip_id}/expenses/{expense_id}")
def delete_expense(trip_id: int, expense_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    
    # Buscamos el gasto asegurándonos que pertenezca al usuario y al viaje
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.trip_id == trip_id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    # Seguridad: Solo el usuario que creó el gasto puede borrarlo
    if expense.user_id != user.id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar este gasto")

    db.delete(expense)
    db.commit()
    return {"message": "Gasto eliminado correctamente"}

# --- Editar un gasto ---
@router.put("/{trip_id}/expenses/{expense_id}")
def update_expense(trip_id: int, expense_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.trip_id == trip_id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    # Seguridad: Solo el usuario que creó el gasto puede editarlo
    if expense.user_id != user.id:
        raise HTTPException(status_code=403, detail="No autorizado para editar este gasto")

    # Actualizar campos
    expense.name = payload.get("name", expense.name)
    expense.category = payload.get("category", expense.category)
    expense.amount = payload.get("amount", expense.amount)
    
    if payload.get("date"):
        try:
            expense.date = datetime.strptime(payload.get("date"), "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido (use YYYY-MM-DD)")

    db.commit()
    db.refresh(expense)
    
    return {
        "id": expense.id,
        "name": expense.name,
        "category": expense.category,
        "amount": expense.amount,
        "date": str(expense.date),
    }

# --- Exportar gastos como PDF ---
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

    elements.append(Paragraph(f"Gastos del viaje: {trip.name}", styles["Title"]))
    elements.append(Spacer(1, 12))

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


# --- Unirse a un viaje (solo premium) ---
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
    """
    Calcula saldos individuales tipo Splitwise:
    - Cada participante puede haber cargado gastos.
    - Se calcula cuánto debería haber aportado y el balance final.
    """
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # Asegurar que el usuario esté agregado como participante
    participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
    if not participant:
        db.add(models.TripParticipant(trip_id=trip_id, user_id=user.id))
        db.commit()

    # --- Obtener participantes y gastos ---
    participants = db.query(models.TripParticipant).filter_by(trip_id=trip_id).all()
    if not participants:
        raise HTTPException(status_code=400, detail="No hay participantes en este viaje")

    expenses = db.query(models.Expense).filter_by(trip_id=trip_id).all()
    if not expenses:
        return {"total": 0, "balances": []}

    # --- Calcular total por usuario ---
    total_gastos = sum(float(e.amount or 0) for e in expenses)
    aportes_por_usuario = {}

    for p in participants:
        user_gastos = db.query(models.Expense).filter_by(trip_id=trip_id, user_id=p.user_id).all()
        total_user = sum(float(e.amount or 0) for e in user_gastos)
        aportes_por_usuario[p.user_id] = total_user

    # --- Calcular cuánto debería haber aportado cada uno ---
    share = round(total_gastos / len(participants), 2)

    balances = []
    for p in participants:
        pagado = aportes_por_usuario.get(p.user_id, 0)
        balance = round(pagado - share, 2)  # positivo = le deben, negativo = debe

        # 🔹 Traer el username asociado a este user_id
        user_obj = db.query(models.User).filter_by(id=p.user_id).first()
        username = user_obj.username if user_obj else f"usuario_{p.user_id}"

        balances.append({
            "username": username,        # 👈 mostramos username en lugar del user_id
            "pagado": pagado,
            "debe_o_recibe": balance
        })

    return {"total": total_gastos, "por_persona": share, "balances": balances}
