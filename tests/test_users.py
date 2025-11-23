import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app import models


def test_upload_profile_photo_success(client: TestClient, auth_headers: dict):
    """Prueba la subida exitosa de una foto de perfil (JPG)."""
    fake_image_bytes = b"fake-jpg-content"
    file = ("test.jpg", io.BytesIO(fake_image_bytes), "image/jpeg")

    response = client.put(
        "/api/users/me/photo", headers=auth_headers, files={"file": file}
    )

    assert response.status_code == 200
    data = response.json()
    assert "profile_picture_url" in data
    assert data["profile_picture_url"].startswith("/static/uploads/")
    assert data["profile_picture_url"].endswith(".jpg")


def test_upload_invalid_file_type(client: TestClient, auth_headers: dict):
    """Prueba que se rechace un tipo de archivo no válido."""
    fake_text_bytes = b"this is not an image"
    file = ("test.txt", io.BytesIO(fake_text_bytes), "text/plain")

    response = client.put(
        "/api/users/me/photo", headers=auth_headers, files={"file": file}
    )

    assert response.status_code == 400
    assert "Tipo de archivo inválido" in response.json()["detail"]


def test_update_travel_preferences(
    client: TestClient, auth_headers: dict, db_session: Session, test_user: models.User
):
    """
    Prueba que un usuario puede actualizar sus preferencias de viaje
    y que se guardan correctamente en la base de datos.
    """
    update_data = {
        "first_name": "Carlos",
        "last_name": "Gomez",
        "birth_date": "1995-08-15",
        "travel_preferences": "Me gusta la playa, el sol y actividades acuáticas. Prefiero destinos cálidos.",
    }

    response = client.put("/api/auth/me", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["first_name"] == "Carlos"
    assert data["last_name"] == "Gomez"
    assert data["birth_date"] == "1995-08-15"
    assert (
        data["travel_preferences"]
        == "Me gusta la playa, el sol y actividades acuáticas. Prefiero destinos cálidos."
    )

    db_session.refresh(test_user)
    assert test_user.first_name == "Carlos"
    assert test_user.last_name == "Gomez"
    assert (
        test_user.travel_preferences
        == "Me gusta la playa, el sol y actividades acuáticas. Prefiero destinos cálidos."
    )


def test_update_partial_profile(client: TestClient, auth_headers: dict):
    """
    Prueba que se pueden actualizar solo algunos campos del perfil
    (actualización parcial).
    """
    update_data = {"travel_preferences": "Prefiero montañas y climas fríos"}

    response = client.put("/api/auth/me", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["travel_preferences"] == "Prefiero montañas y climas fríos"


def test_clear_travel_preferences(
    client: TestClient, auth_headers: dict, db_session: Session, test_user: models.User
):
    """
    Prueba que se pueden borrar las preferencias de viaje
    enviando null o string vacío.
    """
    test_user.travel_preferences = "Prefiero playas"
    db_session.commit()

    update_data = {"travel_preferences": None}

    response = client.put("/api/auth/me", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["travel_preferences"] is None

    db_session.refresh(test_user)
    assert test_user.travel_preferences is None
