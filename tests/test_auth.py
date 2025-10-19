# tests/test_auth.py
from fastapi.testclient import TestClient

# Datos de un usuario de prueba
test_user_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "security_question_1": "¿Mascota?",
    "security_answer_1": "Firulais",
    "security_question_2": "¿Ciudad?",
    "security_answer_2": "Metropolis"
}

def test_register_user_success(client: TestClient):
    """Prueba que un usuario puede registrarse exitosamente."""
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data # ¡Importante! Nunca exponer la contraseña

def test_register_existing_username(client: TestClient):
    """Prueba que no se puede registrar un nombre de usuario duplicado."""
    client.post("/api/auth/register", json=test_user_data) # Registrar primero
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "El nombre de usuario ya existe"

def test_login_success(client: TestClient):
    """Prueba que un usuario registrado puede iniciar sesión."""
    client.post("/api/auth/register", json=test_user_data) # Registrar primero
    
    login_data = {"identifier": "testuser", "password": "testpassword123"}
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient):
    """Prueba que el login falla con una contraseña incorrecta."""
    client.post("/api/auth/register", json=test_user_data)
    
    login_data = {"identifier": "testuser", "password": "wrongpassword"}
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Contraseña o usuario incorrecta."

def test_get_me_success(client: TestClient):
    """Prueba que se puede obtener la información del usuario con un token válido."""
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post("/api/auth/login", json={"identifier": "testuser", "password": "testpassword123"})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_get_me_no_token(client: TestClient):
    """Prueba que no se puede acceder a /me sin un token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token faltante"