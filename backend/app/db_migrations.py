# backend/app/db_migrations.py
from sqlalchemy import text

PUBLICATIONS_COLUMNS = [
    ("place_name", "TEXT"),
    ("country", "TEXT"),
    ("province", "TEXT"),
    ("city", "TEXT"),
    ("address", "TEXT"),
    ("created_at", "TIMESTAMP"),
    ("status", "TEXT"),
    ("created_by_user_id", "INTEGER"),
]

def ensure_min_schema(engine):
    """
    Asegura que la tabla publications tenga las columnas mínimas.
    No borra datos. Para SQLite: agrega columnas faltantes con ALTER TABLE.
    También crea la tabla de favoritos si no existe.
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
                elif col == "status":
                    conn.exec_driver_sql(
                        f'ALTER TABLE publications ADD COLUMN {col} {coltype} DEFAULT "approved"'
                    )
                else:
                    conn.exec_driver_sql(
                        f"ALTER TABLE publications ADD COLUMN {col} {coltype}"
                    )
        
        # Crear tabla de favoritos si no existe
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                publication_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE,
                UNIQUE(user_id, publication_id)
            )
        """)
        
        # Crear índices para la tabla favorites
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_favorites_publication_id ON favorites(publication_id)")
