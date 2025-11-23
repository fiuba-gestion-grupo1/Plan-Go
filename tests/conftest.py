import os

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///./ci_test.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base, get_db
from backend.app.main import app
from backend.app import models, security

DATABASE_URL_TEST = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
    """Crear las tablas una vez por sesión de tests."""
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(scope="function")
def db_session():
    """Sesión limpia por test."""
    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        transaction.commit()

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="module")
def client():
    """Cliente de prueba de FastAPI."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "security_question_1": "Pet's name?",
        "security_answer_1": "Fido",
        "security_question_2": "City of birth?",
        "security_answer_2": "Testville",
    }

@pytest.fixture(scope="function")
def test_user(db_session: TestingSessionLocal, test_user_data: dict):
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
def admin_user(db_session: TestingSessionLocal):
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


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user, test_user_data: dict):
    login_data = {"identifier": test_user_data["email"], "password": test_user_data["password"]}
    response = client.post("/api/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client: TestClient, admin_user):
    """Token Bearer para el admin."""
    resp = client.post("/api/auth/login", json={
        "identifier": admin_user.email,
        "password": "adminpass"
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_uploads():
    """Eliminar SOLO archivos generados por los tests (no tocar los existentes)."""
    uploads_dir = os.path.join("backend", "app", "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    existing_files = set(os.listdir(uploads_dir))
    yield
    current_files = set(os.listdir(uploads_dir))
    new_files = current_files - existing_files
    for filename in new_files:
        path = os.path.join(uploads_dir, filename)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as e:
            print(f"⚠️ No se pudo borrar {path}: {e}")
