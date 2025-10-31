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
    # Usuario básico envía una publicación -> debe quedar en 'pending'
    data = {
        "place_name": "Hotel Usuario",
        "country": "AR",
        "province": "BA",
        "city": "CABA",
        "address": "Calle Usuario 1",
    }
    files = [("photos", _fake_img("u1.jpg"))]
    create = client.post(
        "/api/publications/submit", data=data, files=files, headers=auth_headers
    )
    assert create.status_code == 201, create.text
    created = create.json()
    assert created["status"] == "pending"

    # track file for cleanup
    for url in created["photos"]:
        track_created_files.append(_url_to_abspath(url))

    pub_id = created["id"]

    # Admin ve la publicación pendiente
    pending = client.get("/api/publications/pending", headers=admin_headers)
    assert pending.status_code == 200
    pending_items = pending.json()
    assert any(p["id"] == pub_id for p in pending_items)

    # Admin aprueba la publicación
    apr = client.put(f"/api/publications/{pub_id}/approve", headers=admin_headers)
    assert apr.status_code == 200
    apr_json = apr.json()
    assert apr_json["status"] == "approved"

    # Ahora debe aparecer en la lista pública
    public_list = client.get("/api/publications/public", headers=auth_headers)
    assert public_list.status_code == 200
    items = public_list.json()
    assert any(it["id"] == pub_id and it["status"] == "approved" for it in items)


# def test_user_submit_publication_and_admin_reject(
#     client: TestClient,
#     auth_headers: dict,
#     admin_headers: dict,
#     db_session: Session,
#     track_created_files,
# ):
#     # Usuario básico envía una publicación -> pendiente
#     data = {
#         "place_name": "Hostel Usuario",
#         "country": "AR",
#         "province": "BA",
#         "city": "CABA",
#         "address": "Calle Usuario 2",
#     }
#     files = [("photos", _fake_img("u2.jpg"))]
#     create = client.post(
#         "/api/publications/submit", data=data, files=files, headers=auth_headers
#     )
#     assert create.status_code == 201
#     created = create.json()
#     for url in created["photos"]:
#         track_created_files.append(_url_to_abspath(url))

#     pub_id = created["id"]

#     # Admin rechaza la publicación
#     rej = client.put(f"/api/publications/{pub_id}/reject", headers=admin_headers)
#     assert rej.status_code == 200
#     rej_json = rej.json()
#     assert rej_json["status"] == "rejected"

#     # No debe aparecer en la lista pública
#     public_list = client.get("/api/publications/public", headers=auth_headers)
#     assert public_list.status_code == 200
#     items = public_list.json()
#     assert not any(it["id"] == pub_id for it in items)


# def test_user_request_deletion_and_admin_processes(
#     client: TestClient,
#     auth_headers: dict,
#     admin_headers: dict,
#     db_session: Session,
#     track_created_files,
# ):
#     # Primero creamos una publicación aprobada por admin
#     data = {
#         "place_name": "Hotel Para Borrar",
#         "country": "AR",
#         "province": "BA",
#         "city": "CABA",
#         "address": "Calle Borrar 3",
#     }
#     files = [("photos", _fake_img("d1.jpg"))]
#     create = client.post("/api/publications", data=data, files=files, headers=admin_headers)
#     assert create.status_code == 201
#     created = create.json()
#     for url in created["photos"]:
#         track_created_files.append(_url_to_abspath(url))
#     pub_id = created["id"]

#     # Usuario solicita eliminación
#     req = client.post(f"/api/publications/{pub_id}/request-deletion", headers=auth_headers)
#     assert req.status_code == 200

#     # Admin lista solicitudes pendientes y obtiene el id
#     pending = client.get("/api/publications/deletion-requests/pending", headers=admin_headers)
#     assert pending.status_code == 200
#     pend = pending.json()
#     # encontrar la solicitud para pub_id
#     req_items = [r for r in pend if r["publication_id"] == pub_id]
#     assert len(req_items) == 1
#     req_id = req_items[0]["id"]

#     # Admin rechaza la solicitud -> la publicación debe seguir existiendo
#     rrej = client.put(f"/api/publications/deletion-requests/{req_id}/reject", headers=admin_headers)
#     assert rrej.status_code == 200

#     public_list = client.get("/api/publications/public", headers=auth_headers)
#     assert public_list.status_code == 200
#     items = public_list.json()
#     assert any(it["id"] == pub_id for it in items)

#     # Ahora el usuario vuelve a solicitar eliminación
#     req2 = client.post(f"/api/publications/{pub_id}/request-deletion", headers=auth_headers)
#     assert req2.status_code == 200

#     pending2 = client.get("/api/publications/deletion-requests/pending", headers=admin_headers)
#     assert pending2.status_code == 200
#     pend2 = pending2.json()
#     req_items2 = [r for r in pend2 if r["publication_id"] == pub_id]
#     assert len(req_items2) == 1
#     req_id2 = req_items2[0]["id"]

#     # Admin aprueba la solicitud -> la publicación debe desaparecer
#     rapp = client.put(f"/api/publications/deletion-requests/{req_id2}/approve", headers=admin_headers)
#     assert rapp.status_code == 200

#     public_list_after = client.get("/api/publications/public", headers=auth_headers)
#     assert public_list_after.status_code == 200
#     items_after = public_list_after.json()
#     assert not any(it["id"] == pub_id for it in items_after)
