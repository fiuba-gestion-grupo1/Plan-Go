from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app import models, security


def test_register_user_success(
    client: TestClient, db_session: Session, test_user_data: dict
):
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert "id" in data

    user_in_db = (
        db_session.query(models.User)
        .filter(models.User.email == test_user_data["email"])
        .first()
    )
    assert user_in_db is not None


def test_register_duplicate_email(client: TestClient, test_user):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "password",
            "security_question_1": "q1",
            "security_answer_1": "a1",
            "security_question_2": "q2",
            "security_answer_2": "a2",
        },
    )
    assert response.status_code == 400
    assert "El correo electrónico ya está registrado" in response.json()["detail"]


def test_login_success_with_email(client: TestClient, test_user, test_user_data: dict):
    response = client.post(
        "/api/auth/login",
        json={
            "identifier": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user, test_user_data: dict):
    response = client.post(
        "/api/auth/login",
        json={"identifier": test_user_data["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Contraseña o usuario incorrecta" in response.json()["detail"]


def test_get_me(client: TestClient, auth_headers: dict, test_user_data: dict):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]


def test_update_me(client: TestClient, auth_headers: dict):
    update_data = {
        "first_name": "Test",
        "last_name": "User",
        "birth_date": "2000-01-01",
        "travel_preferences": "Mountains",
    }
    response = client.put("/api/auth/me", headers=auth_headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Test"
    assert data["travel_preferences"] == "Mountains"


def test_change_password_success(
    client: TestClient, auth_headers: dict, test_user_data: dict
):
    new_password = "newpassword123"
    response = client.post(
        "/api/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": test_user_data["password"],
            "new_password": new_password,
        },
    )
    assert response.status_code == 200
    assert "Contraseña actualizada con éxito" in response.json()["message"]

    login_response = client.post(
        "/api/auth/login",
        json={"identifier": test_user_data["email"], "password": new_password},
    )
    assert login_response.status_code == 200


def test_forgot_password_flow(client: TestClient, test_user, test_user_data: dict):

    response_get_q = client.post(
        "/api/auth/forgot-password/get-questions",
        json={"identifier": test_user_data["email"]},
    )
    assert response_get_q.status_code == 200
    questions = response_get_q.json()
    assert questions["security_question_1"] == test_user_data["security_question_1"]

    response_verify_a = client.post(
        "/api/auth/forgot-password/verify-answers",
        json={
            "identifier": test_user_data["email"],
            "security_answer_1": test_user_data["security_answer_1"],
            "security_answer_2": test_user_data["security_answer_2"],
        },
    )
    assert response_verify_a.status_code == 200
    temp_token = response_verify_a.json()["access_token"]

    new_password = "resetpassword456"
    reset_headers = {"Authorization": f"Bearer {temp_token}"}
    response_set_pw = client.post(
        "/api/auth/forgot-password/set-new-password",
        headers=reset_headers,
        json={"new_password": new_password},
    )
    assert response_set_pw.status_code == 200
    assert "Contraseña actualizada con éxito" in response_set_pw.json()["message"]

    final_login_response = client.post(
        "/api/auth/login",
        json={"identifier": test_user_data["email"], "password": new_password},
    )
    assert final_login_response.status_code == 200
