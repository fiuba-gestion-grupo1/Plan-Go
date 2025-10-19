# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

from backend.app.db import Base, get_db
from backend.app.main import app
from backend.app import models, security

#base de datos SQLite en memoria para los tests
DATABASE_URL_TEST = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Usar StaticPool para SQLite en memoria
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Fixture para crear las tablas una vez por sesión de tests."""
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(scope="function")
def db_session():
    """Fixture para obtener una sesión de base de datos por cada test."""
    # Abre una conexión y limpia todas las tablas
    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        transaction.commit()

    # Crea una nueva sesión para el test
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="module")
#cliente de prueba de FastAPI
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def test_user_data():
    """Datos de un usuario de prueba."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "security_question_1": "Pet's name?",
        "security_answer_1": "Fido",
        "security_question_2": "City of birth?",
        "security_answer_2": "Testville"
    }

@pytest.fixture(scope="function")
def test_user(db_session: TestingSessionLocal, test_user_data: dict):
    """Crea un usuario en la DB y lo devuelve."""
    user = models.User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=security.hash_password(test_user_data["password"]),
        security_question_1=test_user_data["security_question_1"],
        hashed_answer_1=security.hash_password(test_user_data["security_answer_1"]),
        security_question_2=test_user_data["security_question_2"],
        hashed_answer_2=security.hash_password(test_user_data["security_answer_2"]),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user, test_user_data: dict):
    """Obtiene un token de autenticación para el usuario de prueba."""
    login_data = {
        "identifier": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}