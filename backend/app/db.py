from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plan_go.db")

if DATABASE_URL.startswith("sqlite"):
    # Extrae la ruta del archivo de la URL
    db_file_path = DATABASE_URL.split("///")[1]
    # Extrae el directorio del archivo
    db_directory = os.path.dirname(db_file_path)
    # Crea el directorio si no existe
    if db_directory:
        os.makedirs(db_directory, exist_ok=True)
        
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
