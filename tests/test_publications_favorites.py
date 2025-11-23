"""
Tests para funcionalidad de favoritos en publicaciones.
Un usuario normal puede marcar/desmarcar publicaciones como favoritas.
"""
import io
import os
from typing import List
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.api.publications import UPLOAD_DIR

def _url_to_abspath(url: str) -> str:
    """
    Convierte '/static/uploads/publications/xxx.jpg' -> ruta absoluta
    'backend/app/static/uploads/publications/xxx.jpg'
    """
    filename = url.split("/static/uploads/publications/")[-1]
    return os.path.join(UPLOAD_DIR, filename)


def _fake_img(name: str = "test.jpg", mime: str = "image/jpeg") -> tuple:
    """Pequeño archivo 'imagen' en memoria."""
    return (name, io.BytesIO(b"fake-image-bytes"), mime)


@pytest.fixture
def track_created_files():
    """Colecciona rutas absolutas que un test vaya creando, y las borra al final."""
    paths: List[str] = []
    yield paths
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

def test_user_can_toggle_favorite_and_see_in_list(
    client: TestClient,
    admin_headers: dict,
    auth_headers: dict,
    db_session: Session,
    track_created_files
):
    """
    Un usuario normal puede:
    1. Marcar una publicación como favorita (toggle)
    2. Verla en su lista de favoritos
    3. Desmarcarla (toggle otra vez)
    """
    data = {
        "place_name": "Hotel Favorito",
        "country": "Argentina",
        "province": "Buenos Aires",
        "city": "Mar del Plata",
        "address": "Av. Costanera 123",
        "description": "Descripción del Hotel Favorito",
    }
    files = [("photos", _fake_img("hotel.jpg"))]
    create_resp = client.post("/api/publications", data=data, files=files, headers=admin_headers)
    assert create_resp.status_code == 201
    pub = create_resp.json()
    pub_id = pub["id"]
    
    for url in pub["photos"]:
        track_created_files.append(_url_to_abspath(url))

    fav_resp = client.post(f"/api/publications/{pub_id}/favorite", headers=auth_headers)
    assert fav_resp.status_code == 200
    assert fav_resp.json()["is_favorite"] is True

    favorite = db_session.query(models.Favorite).filter_by(publication_id=pub_id).first()
    assert favorite is not None

    list_resp = client.get("/api/publications/favorites", headers=auth_headers)
    assert list_resp.status_code == 200
    favorites = list_resp.json()
    assert len(favorites) == 1
    assert favorites[0]["id"] == pub_id
    assert favorites[0]["place_name"] == "Hotel Favorito"

    unfav_resp = client.post(f"/api/publications/{pub_id}/favorite", headers=auth_headers)
    assert unfav_resp.status_code == 200
    assert unfav_resp.json()["is_favorite"] is False

    favorite_deleted = db_session.query(models.Favorite).filter_by(publication_id=pub_id).first()
    assert favorite_deleted is None

    empty_list = client.get("/api/publications/favorites", headers=auth_headers)
    assert empty_list.status_code == 200
    assert len(empty_list.json()) == 0
