import pytest
from fastapi import status
from backend.app import models

def create_pub(db, **kw):
    """
    Crea una Publication con campos mínimos y los usados por el score().
    """
    p = models.Publication(
        place_name=kw.get("place_name", "Lugar"),
        country=kw.get("country", "AR"),
        province=kw.get("province", "Buenos Aires"),
        city=kw.get("city", "CABA"),
        address=kw.get("address", "Av. X 123"),
        continent=kw.get("continent"),
        climate=kw.get("climate"),
        activities=kw.get("activities"),
        cost_per_day=kw.get("cost_per_day"),
        duration_min=kw.get("duration_min"),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def set_pref(db, user_id: int, **kw):
    """
    Crea/guarda UserPreference para el usuario dado.
    """
    pref = models.UserPreference(
        user_id=user_id,
        budget_min=kw.get("budget_min"),
        budget_max=kw.get("budget_max"),
        climates=kw.get("climates"),
        activities=kw.get("activities"),
        continents=kw.get("continents"),
        duration_min_days=kw.get("duration_min_days"),
        duration_max_days=kw.get("duration_max_days"),
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref

def test_requires_auth(client):
    """
    Debe requerir autenticación (sin token => 401/403).
    """
    r = client.get("/api/suggestions")
    assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_no_preferences_returns_empty(client, db_session, test_user, auth_headers):
    """
    Si el usuario no tiene preferencias => []
    """
    create_pub(db_session, place_name="A", continent="américa")
    create_pub(db_session, place_name="B", continent="europa")

    r = client.get("/api/suggestions", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []

def test_title_fallback_uses_place_name(client, db_session, test_user, auth_headers):
    """
    El título en la respuesta usa place_name cuando no existe title en el modelo.
    """
    set_pref(db_session, test_user.id, continents=["américa"])
    pub = create_pub(db_session, place_name="Cataratas", continent="américa")

    r = client.get("/api/suggestions", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert any(item["id"] == pub.id and item["place_name"] == "Cataratas" for item in data)
