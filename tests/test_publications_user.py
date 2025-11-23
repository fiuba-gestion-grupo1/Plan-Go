import io
import os
from typing import List, Optional
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.api.publications import UPLOAD_DIR


def _fake_img(name: str = "test.jpg", mime: str = "image/jpeg") -> tuple:
    return (name, io.BytesIO(b"fake-image-bytes"), mime)


def _url_to_abspath(url: str) -> str:
    filename = url.split("/static/uploads/publications/")[-1]
    return os.path.join(UPLOAD_DIR, filename)


@pytest.fixture
def track_created_files():
    paths: List[str] = []
    yield paths
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def test_user_submit_publication_and_admin_approve(
    client: TestClient,
    auth_headers: dict,
    admin_headers: dict,
    db_session: Session,
    track_created_files,
):
    data = {
        "place_name": "Hotel Usuario",
        "country": "AR",
        "province": "BA",
        "city": "CABA",
        "address": "Calle Usuario 1",
        "description": "Hotel enviado por el usuario",
    }
    files = [("photos", _fake_img("u1.jpg"))]
    create = client.post(
        "/api/publications/submit", data=data, files=files, headers=auth_headers
    )
    assert create.status_code == 201, create.text
    created = create.json()
    assert created["status"] == "pending"

    for url in created["photos"]:
        track_created_files.append(_url_to_abspath(url))

    pub_id = created["id"]

    pending = client.get("/api/publications/pending", headers=admin_headers)
    assert pending.status_code == 200
    pending_items = pending.json()
    assert any(p["id"] == pub_id for p in pending_items)

    apr = client.put(f"/api/publications/{pub_id}/approve", headers=admin_headers)
    assert apr.status_code == 200
    apr_json = apr.json()
    assert apr_json["status"] == "approved"

    public_list = client.get("/api/publications/public", headers=auth_headers)
    assert public_list.status_code == 200
    items = public_list.json()
    assert any(it["id"] == pub_id and it["status"] == "approved" for it in items)
