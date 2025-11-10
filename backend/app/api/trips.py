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


@router.get("")
def get_my_trips(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # viajes que el usuario creó
    own_trips = db.query(models.Trip).filter_by(user_id=user.id).all()
    
    # viajes donde es participante
    participant_links = db.query(models.TripParticipant).filter_by(user_id=user.id).all()
    participant_trips = [p.trip for p in participant_links if p.trip is not None]

    # combinar y evitar duplicados
    all_trips = {t.id: t for t in (own_trips + participant_trips)}.values()

    return [
        {
            "id": t.id,
            "name": t.name,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "created_at": t.created_at,
            "participants_count": len(t.participants)
        }
        for t in all_trips
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

    # ✅ Convertir strings a fechas (si existen)
    start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
    end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None

    # ✅ Crear viaje
    trip = models.Trip(
        user_id=user.id,
        name=name,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(trip)
    db.flush()  # 👈 asegura que trip.id exista sin commit todavía

    # ✅ Agregar creador como participante (mismo flush)
    db.add(models.TripParticipant(trip_id=trip.id, user_id=user.id))
    db.commit()  # 👈 commit único, sincronizado

    db.refresh(trip)

    return {
        "id": trip.id,
        "name": trip.name,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
    }



@router.post("/{trip_id}/invite")
def invite_user_to_trip(
    trip_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # ✅ Solo usuarios premium pueden invitar
    if user.role != "premium":
        raise HTTPException(status_code=403, detail="Solo los usuarios premium pueden enviar invitaciones.")

    username_to_invite = payload.get("username")
    if not username_to_invite:
        raise HTTPException(status_code=400, detail="Debe indicar el nombre de usuario a invitar")

    # 🔍 Buscar el viaje
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # ✅ El invitador debe ser participante o el creador
    inviter_participant = db.query(models.TripParticipant).filter_by(
        trip_id=trip_id, user_id=user.id
    ).first()

    # 🔹 Si no figura como participante pero es el creador, lo agregamos implícitamente
    if not inviter_participant and trip.user_id == user.id:
        inviter_participant = models.TripParticipant(trip_id=trip_id, user_id=user.id)
        db.add(inviter_participant)
        db.commit()  # 👈 asegura persistencia inmediata

    if not inviter_participant:
        raise HTTPException(
            status_code=403,
            detail="Solo los participantes del viaje pueden invitar a otros usuarios."
        )

    # 🔍 Buscar usuario a invitar
    invited_user = db.query(models.User).filter_by(username=username_to_invite).first()
    if not invited_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 🚫 No puede invitarse a sí mismo
    if invited_user.id == user.id:
        raise HTTPException(status_code=400, detail="No podés invitarte a vos mismo")

    # ✅ Solo se pueden invitar usuarios premium
    if invited_user.role != "premium":
        raise HTTPException(status_code=403, detail="Solo se pueden invitar usuarios premium")

    # 🚫 Si ya es participante del viaje, no se lo puede invitar de nuevo
    already_participant = db.query(models.TripParticipant).filter_by(
        trip_id=trip_id, user_id=invited_user.id
    ).first()
    if already_participant:
        raise HTTPException(status_code=400, detail="El usuario ya es participante de este viaje")

    # 🚫 Si ya existió una invitación (en cualquier estado), no se lo puede invitar otra vez
    any_invitation = db.query(models.TripInvitation).filter_by(
        trip_id=trip_id,
        invited_user_id=invited_user.id
    ).first()
    if any_invitation:
        raise HTTPException(status_code=400, detail="Ya existe una invitación registrada para este usuario en este viaje")

    # ✅ Crear nueva invitación
    invitation = models.TripInvitation(
        trip_id=trip_id,
        invited_user_id=invited_user.id,
        invited_by_user_id=user.id,
        status="pending"
    )

    db.add(invitation)
    db.commit()

    return {"message": f"Invitación enviada a {username_to_invite}"}



@router.get("/invitations")
def get_my_invitations(db: Session = Depends(get_db), user=Depends(get_current_user)):
    invites = db.query(models.TripInvitation).filter_by(invited_user_id=user.id, status="pending").all()
    return [
        {
            "id": inv.id,
            "trip_id": inv.trip_id,
            "trip_name": inv.trip.name,
            "invited_by": inv.invited_by_user.username,
            "created_at": inv.created_at
        }
        for inv in invites
    ]


@router.post("/invitations/{invitation_id}/respond")
def respond_to_invitation(
    invitation_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    action = payload.get("action")  # "accept" o "reject"
    if action not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="Acción inválida")

    invitation = db.query(models.TripInvitation).filter_by(
        id=invitation_id,
        invited_user_id=user.id
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")

    # Si ya fue respondida, no permitir re-responder (y mantenemos la unicidad de intentos)
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Esta invitación ya fue respondida previamente")

    if action == "accept":
        # Marcar aceptada
        invitation.status = "accepted"

        # ✅ Agregar participante solo si no existe
        existing_participant = db.query(models.TripParticipant).filter_by(
            trip_id=invitation.trip_id, user_id=user.id
        ).first()
        if not existing_participant:
            db.add(models.TripParticipant(trip_id=invitation.trip_id, user_id=user.id))

        db.commit()
        return {"message": "Invitación aceptada correctamente"}

    # Rechazo
    invitation.status = "rejected"
    db.commit()
    return {"message": "Invitación rechazada correctamente"}


# --- Editar un viaje ---
@router.put("/{trip_id}")
def update_trip(trip_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # 🔒 Permisos: el creador o cualquier participante aceptado pueden editar
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")

    # Actualizar campos
    trip.name = payload.get("name", trip.name)
    
    # Convertir fechas si vienen en el payload
    if "start_date" in payload:
        start = payload.get("start_date")
        trip.start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
    
    if "end_date" in payload:
        end = payload.get("end_date")
        trip.end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None

    db.commit()
    db.refresh(trip)
    
    return {
        "id": trip.id,
        "name": trip.name,
        "start_date": trip.start_date,
        "end_date": trip.end_date
    }

# --- Eliminar un viaje (y todos sus gastos/participantes asociados) ---
@router.delete("/{trip_id}")
def delete_trip(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # 🔒 Permisos: el creador o cualquier participante aceptado pueden eliminar
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")

    # 🔽 Eliminar todas las entidades relacionadas con este viaje
    db.query(models.Expense).filter(models.Expense.trip_id == trip_id).delete()
    db.query(models.TripParticipant).filter(models.TripParticipant.trip_id == trip_id).delete()
    db.query(models.TripInvitation).filter(models.TripInvitation.trip_id == trip_id).delete()  # 👈 ESTA ES LA CLAVE

    db.delete(trip)
    db.commit()

    return {"message": "Viaje eliminado correctamente"}



# --- Obtener gastos de un viaje ---
@router.get("/{trip_id}/expenses")
def get_trip_expenses(trip_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Buscar el viaje sin filtrar por usuario todavía
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # 🔒 Verificar permisos de acceso:
    # El creador siempre puede ver los gastos.
    # Los participantes aceptados también pueden verlos.
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")

    # Si pasa la validación, devolver los gastos
    return [
        {
            "id": e.id,
            "name": e.name,
            "category": e.category,
            "amount": e.amount,
            "date": e.date,
        }
        for e in trip.expenses
    ]


# --- Agregar gasto ---
@router.post("/{trip_id}/expenses")
def add_expense(trip_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # 🔒 Permisos: el creador o cualquier participante aceptado pueden agregar gastos
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")


    try:
        date_obj = datetime.strptime(payload.get("date"), "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (use YYYY-MM-DD)")

    # --- VALIDACIÓN DE FECHAS ---
    if trip.start_date and date_obj < trip.start_date:
        raise HTTPException(
            status_code=400, 
            detail=f"La fecha del gasto ({date_obj}) no puede ser anterior al inicio del viaje ({trip.start_date})."
        )
    
    if trip.end_date and date_obj > trip.end_date:
        raise HTTPException(
            status_code=400, 
            detail=f"La fecha del gasto ({date_obj}) no puede ser posterior al fin del viaje ({trip.end_date})."
        )

    # --- VALIDACIÓN DE MONTO ---
    try:
        amount_val = float(payload.get("amount", 0))
        if amount_val < 0:
            raise HTTPException(status_code=400, detail="El monto del gasto no puede ser negativo.")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="El monto debe ser un número válido.")

    exp = models.Expense(
        trip_id=trip.id,
        user_id=user.id,  
        name=payload.get("name"),
        category=payload.get("category"),
        amount=amount_val, 
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

# --- Eliminar un gasto ---
@router.delete("/{trip_id}/expenses/{expense_id}")
def delete_expense(trip_id: int, expense_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Buscar el gasto
    expense = db.query(models.Expense).filter_by(id=expense_id, trip_id=trip_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    # Buscar el viaje
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # 🔒 Permisos:
    # El creador o cualquier participante aceptado pueden eliminar cualquier gasto.
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")

    # Si pasa la validación, eliminar el gasto
    db.delete(expense)
    db.commit()
    return {"message": "Gasto eliminado correctamente"}

# --- Editar un gasto ---
@router.put("/{trip_id}/expenses/{expense_id}")
def update_expense(trip_id: int, expense_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.trip_id == trip_id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")


    # 🔒 Permisos:
    # El creador o cualquier participante aceptado pueden editar cualquier gasto.
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")



    expense.name = payload.get("name", expense.name)
    expense.category = payload.get("category", expense.category)
    
    new_amount_val = expense.amount  # Valor por defecto es el actual
    
    if "amount" in payload: # Solo validamos si se está intentando cambiar el monto
        try:
            new_amount_val = float(payload.get("amount"))
            if new_amount_val < 0:
                raise HTTPException(status_code=400, detail="El monto del gasto no puede ser negativo.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="El monto debe ser un número válido.")
    
    expense.amount = new_amount_val # Asignamos el monto validado (o el original si no cambió)
    
    new_date_obj = expense.date  # Por defecto, la fecha que ya tiene
    
    if payload.get("date"):
        try:
            new_date_obj = datetime.strptime(payload.get("date"), "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido (use YYYY-MM-DD)")

    # --- VALIDACIÓN DE FECHAS ---
    if trip.start_date and new_date_obj < trip.start_date:
        raise HTTPException(
            status_code=400, 
            detail=f"La fecha del gasto ({new_date_obj}) no puede ser anterior al inicio del viaje ({trip.start_date})."
        )
    
    if trip.end_date and new_date_obj > trip.end_date:
        raise HTTPException(
            status_code=400, 
            detail=f"La fecha del gasto ({new_date_obj}) no puede ser posterior al fin del viaje ({trip.end_date})."
        )
    expense.date = new_date_obj

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


# Buscar el viaje sin limitar por user_id
    trip = db.query(models.Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    # 🔒 Permisos: creador o participante aceptado pueden exportar
    if trip.user_id != user.id:
        is_participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not is_participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")

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

    # --- Validar acceso al cálculo de saldos ---
    # El creador del viaje siempre puede ver y calcular
    if trip.user_id != user.id:
        participant = db.query(models.TripParticipant).filter_by(trip_id=trip_id, user_id=user.id).first()
        if not participant:
            raise HTTPException(status_code=403, detail="No sos participante de este viaje")


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
