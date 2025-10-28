# backend/app/db_migrations.py
from sqlalchemy import text

# backend/app/db_migrations.py

PUBLICATIONS_COLUMNS = [
    ("place_name", "TEXT"),
    ("country", "TEXT"),
    ("province", "TEXT"),
    ("city", "TEXT"),
    ("address", "TEXT"),
    ("created_at", "TIMESTAMP"),
    # Campos de rating / enriquecimiento
    ("rating_avg", "REAL"),
    ("rating_count", "INTEGER"),
    ("continent", "TEXT"),
    ("climate", "TEXT"),
    ("activities", "TEXT"),
    ("cost_per_day", "REAL"),
    ("duration_days", "INTEGER"),
    # Campos de workflow/autoría
    ("status", "TEXT"),
    ("created_by_user_id", "INTEGER"),
]


def ensure_min_schema(engine):
    """
    Asegura que la tabla publications tenga las columnas mínimas.
    No borra datos. Para SQLite: agrega columnas faltantes con ALTER TABLE.
    También crea las tablas auxiliares si no existen (favorites, deletion_requests).
    """
    with engine.begin() as conn:
        # Obtener columnas existentes de 'publications'
        pragma = conn.exec_driver_sql("PRAGMA table_info(publications)").fetchall()
        existing = {row[1] for row in pragma}  # nombre de la columna en idx 1

        # Agregar columnas faltantes
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

        # --- Tabla de favoritos ---
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                publication_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE,
                UNIQUE(user_id, publication_id)
            )
        """
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_favorites_publication_id ON favorites(publication_id)"
        )

        # --- Tabla de solicitudes de eliminación ---
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS deletion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id INTEGER NOT NULL,
                requested_by_user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT (datetime('now')),
                resolved_at TIMESTAMP,
                FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE,
                FOREIGN KEY (requested_by_user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_deletion_requests_publication_id ON deletion_requests(publication_id)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_deletion_requests_status ON deletion_requests(status)"
        )
