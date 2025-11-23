from sqlalchemy import text

PUBLICATIONS_COLUMNS = [
    ("place_name", "TEXT"),
    ("country", "TEXT"),
    ("province", "TEXT"),
    ("city", "TEXT"),
    ("address", "TEXT"),
    ("created_at", "TIMESTAMP"),
    ("rating_avg", "REAL"),
    ("rating_count", "INTEGER"),
    ("continent", "TEXT"),
    ("climate", "TEXT"),
    ("activities", "TEXT"),
    ("cost_per_day", "REAL"),
    ("duration_min", "INTEGER"),
    ("status", "TEXT"),
    ("rejection_reason", "TEXT"),
    ("created_by_user_id", "INTEGER"),
]


def ensure_min_schema(engine):
    """
    Asegura que la tabla publications tenga las columnas mínimas.
    No borra datos. Para SQLite: agrega columnas faltantes con ALTER TABLE.
    También crea las tablas auxiliares si no existen (favorites, deletion_requests).
    """
    with engine.begin() as conn:
        pragma = conn.exec_driver_sql("PRAGMA table_info(publications)").fetchall()
        existing = {row[1] for row in pragma}

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

        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS deletion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id INTEGER NOT NULL,
                requested_by_user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                reason TEXT,
                rejection_reason TEXT,
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

        itinerary_check = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='itineraries'"
        ).fetchone()
        
        if itinerary_check:
            pragma_itinerary = conn.exec_driver_sql("PRAGMA table_info(itineraries)").fetchall()
            existing_itinerary = {row[1] for row in pragma_itinerary}
            
            if "publication_ids" not in existing_itinerary:
                conn.exec_driver_sql(
                    "ALTER TABLE itineraries ADD COLUMN publication_ids TEXT"
                )
            
            if "cant_persons" not in existing_itinerary:
                conn.exec_driver_sql(
                    "ALTER TABLE itineraries ADD COLUMN cant_persons INTEGER DEFAULT 1"
                )
                
            if "comments" not in existing_itinerary:
                conn.exec_driver_sql(
                    "ALTER TABLE itineraries ADD COLUMN comments TEXT"
                )

        pragma_deletion = conn.exec_driver_sql("PRAGMA table_info(deletion_requests)").fetchall()
        existing_deletion = {row[1] for row in pragma_deletion}
        
        if "rejection_reason" not in existing_deletion:
            conn.exec_driver_sql(
                "ALTER TABLE deletion_requests ADD COLUMN rejection_reason TEXT"
            )
        
        if "reason" not in existing_deletion:
            conn.exec_driver_sql(
                "ALTER TABLE deletion_requests ADD COLUMN reason TEXT"
            )

        user_points_check = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_points'"
        ).fetchone()
        
        if not user_points_check:
            conn.exec_driver_sql("""
                CREATE TABLE user_points (
                    user_id INTEGER PRIMARY KEY,
                    total_points INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_user_points_user_id ON user_points(user_id)"
            )

        points_transactions_check = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='points_transactions'"
        ).fetchone()
        
        if not points_transactions_check:
            conn.exec_driver_sql("""
                CREATE TABLE points_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    points INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    description TEXT,
                    reference_id INTEGER,
                    created_at TIMESTAMP DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_points_transactions_user_id ON points_transactions(user_id)"
            )
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_points_transactions_created_at ON points_transactions(created_at)"
            )
