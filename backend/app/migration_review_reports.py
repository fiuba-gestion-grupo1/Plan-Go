#!/usr/bin/env python3
"""
Migración para agregar funcionalidad de reportes de reseñas
- Agrega columna 'status' a la tabla 'reviews' 
- Crea tabla 'review_reports' para gestionar reportes de reseñas
"""
import sqlite3
import os

def run_migration():
    # Buscar la base de datos
    db_path = None
    possible_paths = [
        "plan_go.db",
        "sql_app.db",
        "plango.db",
        "app.db",
        "../plan_go.db",
        "../sql_app.db",
        "../plango.db",
        "../app.db",
        "/app/data/plan_go.db",
        "data/plan_go.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No se encontró la base de datos. Posibles ubicaciones:")
        for path in possible_paths:
            print(f"   - {os.path.abspath(path)}")
        return False

    print(f"📂 Usando base de datos: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna 'status' ya existe en reviews
        cursor.execute("PRAGMA table_info(reviews)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'status' not in columns:
            print("➕ Agregando columna 'status' a tabla 'reviews'...")
            cursor.execute("""
                ALTER TABLE reviews 
                ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved'
            """)
            
            # Crear índice para la nueva columna
            cursor.execute("""
                CREATE INDEX ix_reviews_status ON reviews (status)
            """)
            print("✅ Columna 'status' agregada con éxito")
        else:
            print("ℹ️  Columna 'status' ya existe en tabla 'reviews'")
        
        # Verificar si la tabla review_reports ya existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='review_reports'
        """)
        
        if not cursor.fetchone():
            print("➕ Creando tabla 'review_reports'...")
            cursor.execute("""
                CREATE TABLE review_reports (
                    id INTEGER PRIMARY KEY,
                    review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
                    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    reason VARCHAR(100) NOT NULL,
                    comments TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    rejection_reason TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    UNIQUE(review_id, reporter_id)
                )
            """)
            
            # Crear índices
            cursor.execute("CREATE INDEX ix_review_reports_review_id ON review_reports (review_id)")
            cursor.execute("CREATE INDEX ix_review_reports_reporter_id ON review_reports (reporter_id)")
            cursor.execute("CREATE INDEX ix_review_reports_status ON review_reports (status)")
            
            print("✅ Tabla 'review_reports' creada con éxito")
        else:
            print("ℹ️  Tabla 'review_reports' ya existe")
        
        conn.commit()
        conn.close()
        
        print("🎉 Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    run_migration()