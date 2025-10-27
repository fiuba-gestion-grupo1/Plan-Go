# backend/app/db_migrations.py
from sqlalchemy import text

PUBLICATIONS_COLUMNS = [
    ("place_name", "TEXT"),
    ("country", "TEXT"),
    ("province", "TEXT"),
    ("city", "TEXT"),
    ("address", "TEXT"),
    ("created_at", "TIMESTAMP"),
    ("rating_avg", "REAL"),     # nuevo
    ("rating_count", "INTEGER"),  # 👈 faltaba esta coma
    ("continent", "TEXT"),        # 👇 campos nuevos
    ("climate", "TEXT"),
    ("activities", "TEXT"),
    ("cost_per_day", "REAL"),
    ("duration_days", "INTEGER"),
]

def ensure_min_schema(engine):
    """
    Asegura que la tabla publications tenga las columnas mínimas.
    No borra datos. Para SQLite: agrega columnas faltantes con ALTER TABLE.
    """
    with engine.begin() as conn:
        # si no existe la tabla, la crea el ORM en startup (create_all).
        # acá solo nos preocupa agregar faltantes.
        # obtener columnas existentes
        pragma = conn.exec_driver_sql("PRAGMA table_info(publications)").fetchall()
        existing = {row[1] for row in pragma}  # nombre de la columna en idx 1

        # agregar faltantes
        for col, coltype in PUBLICATIONS_COLUMNS:
            if col not in existing:
                if col == "created_at":
                    conn.exec_driver_sql(
                        f'ALTER TABLE publications ADD COLUMN {col} {coltype} DEFAULT (datetime("now"))'
                    )
                else:
                    conn.exec_driver_sql(
                        f"ALTER TABLE publications ADD COLUMN {col} {coltype}"
                    )
