import io
import os
from typing import List
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app import models, security
from backend.app.api.publications import UPLOAD_DIR

def _url_to_abspath(url: str) -> str:
    """
    Convierte '/static/uploads/publications/xxx.jpg' -> ruta absoluta
    'backend/app/static/uploads/publications/xxx.jpg'
    """
    filename = url.split("/static/uploads/publications/")[-1]
    return os.path.join(UPLOAD_DIR, filename)


def _fake_img(name: str = "test.jpg", mime: str = "image/jpeg") -> tuple:
    """Pequeño archivo 'imagen' en memoria (el contenido no se valida)."""
    return (name, io.BytesIO(b"fake-image-bytes"), mime)



@pytest.fixture
def admin_user(db_session: Session):
    """Crea un usuario con rol admin en la DB de test."""
    user = models.User(
        username="admin_test",
        email="admin@test.local",
        role="admin",
        hashed_password=security.hash_password("adminpass"),
        security_question_1="q1",
        hashed_answer_1=security.hash_password("a1"),
        security_question_2="q2",
        hashed_answer_2=security.hash_password("a2"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(client: TestClient, admin_user) -> dict:
    """Token Bearer para el admin."""
    resp = client.post("/api/auth/login", json={
        "identifier": admin_user.email,
        "password": "adminpass"
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def track_created_files():
    """
    Colecciona rutas absolutas que un test vaya creando, y las borra al final.
    Se usa por si un test crea archivos y falla antes del delete.
    """
    paths: List[str] = []
    yield paths
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def test_admin_create_publication_with_photos_success(
    client: TestClient, admin_headers: dict, db_session: Session, track_created_files
):
    data = {
        "place_name": "FIUBA - Paseo Colón",
        "country": "Argentina",
        "province": "Buenos Aires",
        "city": "San Telmo",
        "address": "Av. Paseo Colón 850",
        "description": "Sede FIUBA Paseo Colón",
    }
    files = [
        ("photos", _fake_img("a.jpg", "image/jpeg")),
        ("photos", _fake_img("b.png", "image/png")),
        ("photos", _fake_img("c.webp", "image/webp")),
    ]

    resp = client.post("/api/publications", data=data, files=files, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["place_name"] == data["place_name"]
    assert len(payload["photos"]) == 3

    pub = db_session.query(models.Publication).filter_by(id=payload["id"]).first()
    assert pub is not None
    assert len(pub.photos) == 3

    for url in payload["photos"]:
        abs_path = _url_to_abspath(url)
        track_created_files.append(abs_path)
        assert os.path.exists(abs_path)


def test_admin_create_publication_rejects_too_many_photos(client: TestClient, admin_headers: dict):
    data = {
        "place_name": "Lugar X",
        "country": "AR",
        "province": "BA",
        "city": "CABA",
        "address": "Calle 123",
        "description": "Lugar X con muchas fotos",
    }
    files = [
        ("photos", _fake_img("1.jpg")),
        ("photos", _fake_img("2.jpg")),
        ("photos", _fake_img("3.jpg")),
        ("photos", _fake_img("4.jpg")),
        ("photos", _fake_img("5.jpg")),
    ]
    resp = client.post("/api/publications", data=data, files=files, headers=admin_headers)
    assert resp.status_code == 400
    assert "Máximo 4 fotos" in resp.json()["detail"]


def test_admin_create_publication_rejects_invalid_mime(client: TestClient, admin_headers: dict):
    data = {
        "place_name": "Lugar Y",
        "country": "AR",
        "province": "BA",
        "city": "CABA",
        "address": "Calle 456",
        "description": "Lugar Y con mime inválido",
    }

    files = [("photos", ("bad.txt", io.BytesIO(b"no-image"), "text/plain"))]
    resp = client.post("/api/publications", data=data, files=files, headers=admin_headers)
    assert resp.status_code == 400
    assert "Formato de imagen inválido" in resp.json()["detail"]


def test_list_publications_requires_admin(client: TestClient, auth_headers: dict):
    """Un usuario normal NO puede consumir /api/publications (403)."""
    resp = client.get("/api/publications", headers=auth_headers)
    assert resp.status_code == 403


def test_public_list_returns_items(
    client: TestClient, admin_headers: dict, track_created_files
):
    """Crea una publicación y verifica que aparezca en /api/publications/public."""
    data = {
        "place_name": "Lugar Público",
        "country": "AR",
        "province": "BA",
        "city": "CABA",
        "address": "Calle Publica 1000",
        "description": "Descripción del lugar público",
    }
    files = [("photos", _fake_img("pub.jpg"))]
    create = client.post("/api/publications", data=data, files=files, headers=admin_headers)
    assert create.status_code == 201
    created = create.json()
    for url in created["photos"]:
        track_created_files.append(_url_to_abspath(url))

    resp = client.get("/api/publications/public", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert any(it["id"] == created["id"] for it in items)
