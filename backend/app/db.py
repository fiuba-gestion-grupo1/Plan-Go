from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from sqlalchemy import inspect

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no está seteada. Definila (p.ej. sqlite:///./plan_go.db)"
    )

if DATABASE_URL.startswith("sqlite"):
    db_file_path = DATABASE_URL.split("///")[1]
    db_directory = os.path.dirname(db_file_path)
    if db_directory:
        os.makedirs(db_directory, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_db_info():
    try:
        from . import models

        insp = inspect(engine)
        print(f"[DB] Conectado a: {DATABASE_URL}")
        print(f"[DB] Tablas: {insp.get_table_names()}")
    except Exception as e:
        print(f"[DB] Error inspeccionando DB: {e}")
