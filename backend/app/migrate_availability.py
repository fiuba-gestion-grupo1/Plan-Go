"""
Migración para agregar campos available_days y available_hours a publicaciones
"""

from sqlalchemy import text
from .db import get_db


def migrate_add_availability_fields():
    """
    Agrega las columnas available_days y available_hours a la tabla publications
    """
    db = next(get_db())

    try:
        result = db.execute(text("PRAGMA table_info(publications)")).fetchall()
        existing_columns = [col[1] for col in result]

        if "available_days" not in existing_columns:
            db.execute(text("ALTER TABLE publications ADD COLUMN available_days TEXT"))
            print("✅ Columna available_days agregada")
        else:
            print("ℹ️ Columna available_days ya existe")

        if "available_hours" not in existing_columns:
            db.execute(text("ALTER TABLE publications ADD COLUMN available_hours TEXT"))
            print("✅ Columna available_hours agregada")
        else:
            print("ℹ️ Columna available_hours ya existe")

        db.commit()
        print("🎉 Migración completada exitosamente")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en la migración: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_add_availability_fields()
