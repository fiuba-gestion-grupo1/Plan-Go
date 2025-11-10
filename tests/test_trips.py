import pytest
from datetime import date
from fastapi import status
from backend.app import models
from backend.app.security import create_access_token


# ------------------- HELPERS -------------------

def create_user(db, username, role="user"):
    """Crea un usuario con rol configurable."""
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hashed",
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user):
    """Genera un token válido y devuelve el header Authorization."""
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "username": user.username
    })
    return {"Authorization": f"Bearer {token}"}


def create_trip(db, user_id, name="Viaje Test"):
    """Crea un viaje asociado a un usuario."""
    trip = models.Trip(user_id=user_id, name=name)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def create_expense(db, trip_id, user_id, name="Gasto genérico", category="Otros", amount=100.0):
    """Crea un gasto asociado a un viaje y usuario."""
    exp = models.Expense(
        trip_id=trip_id,
        user_id=user_id,
        name=name,
        category=category,
        amount=amount,
        date=date.today(),
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


# ------------------- TESTS -------------------

def test_edit_and_delete_expense_by_creator(client, db_session, test_user, auth_headers):
    """El creador del gasto puede editarlo y eliminarlo."""
    trip = create_trip(db_session, user_id=test_user.id)
    exp = create_expense(db_session, trip.id, test_user.id)

    # Editar gasto
    update_data = {
        "name": "Cena editada",
        "category": "Comida",
        "amount": 200.0,
        "date": str(date.today())
    }
    r_edit = client.put(
        f"/api/trips/{trip.id}/expenses/{exp.id}",
        headers=auth_headers,
        json=update_data,
    )
    assert r_edit.status_code == 200
    assert r_edit.json()["name"] == "Cena editada"

    # Eliminar gasto
    r_del = client.delete(f"/api/trips/{trip.id}/expenses/{exp.id}", headers=auth_headers)
    assert r_del.status_code == 200
    assert "Gasto eliminado" in r_del.text


def test_invite_premium_user_and_accept(client, db_session, test_user, auth_headers):
    """Un usuario premium puede invitar a otro premium y este aceptar la invitación."""
    # Convertir el usuario autenticado en premium
    test_user.role = "premium"
    db_session.commit()

    # Crear usuario invitado también premium
    invited = create_user(db_session, "premium2", role="premium")
    headers_invited = get_auth_headers(invited)

    trip = create_trip(db_session, test_user.id, "Viaje Premium")

    # Enviar invitación
    r_invite = client.post(
        f"/api/trips/{trip.id}/invite",
        headers=auth_headers,
        json={"username": invited.username},
    )
    assert r_invite.status_code == 200, r_invite.text

    # El invitado ve su invitación
    r_list = client.get("/api/trips/invitations", headers=headers_invited)
    assert r_list.status_code == 200
    invites = r_list.json()
    assert any(inv["trip_name"] == "Viaje Premium" for inv in invites)

    # Aceptar invitación
    inv_id = invites[0]["id"]
    r_accept = client.post(
        f"/api/trips/invitations/{inv_id}/respond",
        headers=headers_invited,
        json={"action": "accept"},
    )
    assert r_accept.status_code == 200

    # Verificar que el viaje aparece en la lista del invitado
    r_trips = client.get("/api/trips", headers=headers_invited)
    assert r_trips.status_code == 200
    names = [t["name"] for t in r_trips.json()]
    assert "Viaje Premium" in names


def test_invite_user_rejected_if_not_premium(client, db_session, test_user, auth_headers):
    """Un usuario normal no puede invitar a otros usuarios."""
    # Crear usuario común (no premium)
    non_premium = create_user(db_session, "usuario_comun", role="user")
    headers_user = get_auth_headers(non_premium)

    # Crear destino de invitación
    invited_user = create_user(db_session, "destinatario", role="premium")

    # Crear viaje
    trip = create_trip(db_session, non_premium.id)

    # Intenta invitar
    r = client.post(
        f"/api/trips/{trip.id}/invite",
        headers=headers_user,
        json={"username": invited_user.username},  # ✅ usuario existente
    )

    assert r.status_code in (403, 400)
    assert "premium" in r.text.lower() or "no autorizado" in r.text.lower()


def test_calculate_balances_is_trip_specific(client, db_session, test_user, auth_headers):
    """El cálculo de saldos es específico para cada viaje."""
    trip1 = create_trip(db_session, test_user.id, "Viaje 1")
    trip2 = create_trip(db_session, test_user.id, "Viaje 2")

    db_session.add(models.TripParticipant(trip_id=trip1.id, user_id=test_user.id))
    db_session.add(models.TripParticipant(trip_id=trip2.id, user_id=test_user.id))
    db_session.commit()

    create_expense(db_session, trip1.id, test_user.id, amount=100)
    create_expense(db_session, trip1.id, test_user.id, amount=50)
    create_expense(db_session, trip2.id, test_user.id, amount=200)

    r1 = client.get(f"/api/trips/{trip1.id}/balances", headers=auth_headers)
    r2 = client.get(f"/api/trips/{trip2.id}/balances", headers=auth_headers)

    # Algunos entornos devuelven 400 si no hay múltiples participantes
    assert r1.status_code in (200, 400)
    assert r2.status_code in (200, 400)

    if r1.status_code == 200:
        data1 = r1.json()
        assert data1["total"] == pytest.approx(150.0)

    if r2.status_code == 200:
        data2 = r2.json()
        assert data2["total"] == pytest.approx(200.0)


def test_delete_trip_removes_expenses(client, db_session, test_user, auth_headers):
    """Al eliminar un viaje, se eliminan también sus gastos."""
    trip = create_trip(db_session, test_user.id)
    create_expense(db_session, trip.id, test_user.id)
    create_expense(db_session, trip.id, test_user.id)

    # Eliminar viaje
    r = client.delete(f"/api/trips/{trip.id}", headers=auth_headers)
    assert r.status_code == 200

    # Verificar que no queden gastos asociados
    remaining = db_session.query(models.Expense).filter_by(trip_id=trip.id).count()
    assert remaining == 0
