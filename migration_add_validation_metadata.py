"""
Migración: Agregar campo validation_metadata a tabla itineraries
"""

import os
from sqlalchemy import create_engine, text


def migrate_add_validation_metadata():
    """Agrega el campo validation_metadata a la tabla itineraries"""

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plan_go.db")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
            SELECT COUNT(*) as count 
            FROM pragma_table_info('itineraries') 
            WHERE name = 'validation_metadata'
        """
            )
        )

        if result.fetchone()[0] == 0:
            print("⏳ Agregando campo validation_metadata a tabla itineraries...")

            connection.execute(
                text(
                    """
                ALTER TABLE itineraries 
                ADD COLUMN validation_metadata TEXT
            """
                )
            )

            connection.commit()
            print("✅ Campo validation_metadata agregado exitosamente")
        else:
            print("✅ Campo validation_metadata ya existe")


if __name__ == "__main__":
    migrate_add_validation_metadata()
    print("🎉 Migración completada")
