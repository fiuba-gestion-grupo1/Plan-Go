import pytest
from fastapi import status
from backend.app import models
from datetime import date


def create_trip(db, user_id, name="Test Trip"):
    """
    Crea un viaje asociado a un usuario.
    """
    trip = models.Trip(user_id=user_id, name=name)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def create_expense(db, trip_id, **kwargs):
    """
    Crea un gasto asociado a un viaje.
    """
    expense = models.Expense(
        trip_id=trip_id,
        name=kwargs.get("name", "Gasto genérico"),
        category=kwargs.get("category", "Otros"),
        amount=kwargs.get("amount", 100.0),
        date=kwargs.get("date", date.today()),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


# ------------------- TESTS -------------------

def test_requires_auth_for_trips(client):
    """
    No debe permitir acceder a /api/trips sin autenticación.
    """
    r = client.get("/api/trips")
    assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_create_trip_and_add_expenses(client, db_session, test_user, auth_headers):
    """
    Crea un viaje, agrega gastos y valida los totales por categoría.
    """
    # Crear viaje
    r_trip = client.post("/api/trips", headers=auth_headers, json={"name": "Europa 2025"})
    assert r_trip.status_code == 200, f"Error creando viaje: {r_trip.text}"
    trip_id = r_trip.json()["id"]

    # Agregar gastos
    expenses = [
        {"name": "Cena en Roma", "category": "Comida", "amount": 50.0, "date": str(date.today())},
        {"name": "Taxi aeropuerto", "category": "Transporte", "amount": 30.0, "date": str(date.today())},
        {"name": "Pizza Napoli", "category": "Comida", "amount": 25.0, "date": str(date.today())},
    ]
    for e in expenses:
        r_exp = client.post(f"/api/trips/{trip_id}/expenses", headers=auth_headers, json=e)
        assert r_exp.status_code == 200, f"Error agregando gasto: {r_exp.text}"

    # Consultar lista de gastos
    r_list = client.get(f"/api/trips/{trip_id}/expenses", headers=auth_headers)
    assert r_list.status_code == 200
    data = r_list.json()
    assert len(data) == 3

    # Calcular totales por categoría
    totals = {}
    for e in data:
        totals[e["category"]] = totals.get(e["category"], 0) + e["amount"]

    assert totals["Comida"] == pytest.approx(75.0)
    assert totals["Transporte"] == pytest.approx(30.0)


def test_expense_requires_fields(client, db_session, test_user, auth_headers):
    """
    Si falta algún campo obligatorio al crear un gasto => 422.
    """
    trip = create_trip(db_session, user_id=test_user.id)
    r = client.post(
        f"/api/trips/{trip.id}/expenses",
        headers=auth_headers,
        json={"name": "Incompleto"},
    )
    assert r.status_code in (400, 422)
