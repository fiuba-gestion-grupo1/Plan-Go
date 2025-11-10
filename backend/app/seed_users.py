# backend/app/seed_users.py
from sqlalchemy.orm import Session

try:
    from backend.app.db import SessionLocal
    from backend.app import models, security
except ImportError:
    print("Error: Ejecutá este script como módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.seed_users")
    raise

def create_or_update_user(db: Session, *, email: str, username: str, password: str, role: str):
    """
    Crea el usuario si no existe. Si existe, actualiza password/role si difieren.
    """
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        changed = False
        # Forzamos role deseado
        if user.role != role:
            user.role = role
            changed = True

        # Re-hasheamos siempre la password por idempotencia simple (opcionalmente podrías verificar)
        user.hashed_password = security.hash_password(password)
        changed = True

        if changed:
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Actualizado: {email} (role={role})")
        else:
            print(f"Sin cambios: {email}")
        return user

    # No existe: crear
    new_user = models.User(
        email=email,
        username=username,
        hashed_password=security.hash_password(password),
        role=role,
        # Campos opcionales (pueden quedar en None):
        first_name=None,
        last_name=None,
        birth_date=None,
        travel_preferences=None,
        security_question_1=None,
        hashed_answer_1=None,
        security_question_2=None,
        hashed_answer_2=None,
        profile_picture_url=None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"Creado: {email} (role={role})")
    return new_user


def seed_users(db: Session):
    print("--- Iniciando Seeding de Usuarios ---")

    create_or_update_user(
        db,
        email="admin@fi.uba.ar",
        username="admin",
        password="password",
        role="admin",
    )

    create_or_update_user(
        db,
        email="normal@fi.uba.ar",
        username="normal",
        password="password",
        role="user",        # usuario normal
    )

    create_or_update_user(
        db,
        email="premium@fi.uba.ar",
        username="premium",
        password="password",
        role="premium",     # usuario premium
    )

    create_or_update_user(
        db,
        email="premium2@fi.uba.ar",
        username="premium2",
        password="password",
        role="premium",     # usuario premium
    )

    print("--- Seeding de Usuarios completado ---")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_users(db)
    except Exception as e:
        print(f"Ocurrió un error durante el seeding de usuarios: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        print("Conexión cerrada.")
