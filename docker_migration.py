#!/usr/bin/env python3
import sys
sys.path.append('/app')
from sqlalchemy import create_engine, text
from backend.app.db import engine

with engine.connect() as connection:
    # Verificar si la columna ya existe
    result = connection.execute(text("""
        SELECT COUNT(*) as count 
        FROM pragma_table_info('itineraries') 
        WHERE name = 'validation_metadata'
    """))
    
    if result.fetchone()[0] == 0:
        print('⏳ Agregando campo validation_metadata...')
        connection.execute(text("""
            ALTER TABLE itineraries 
            ADD COLUMN validation_metadata TEXT
        """))
        connection.commit()
        print('✅ Campo validation_metadata agregado')
    else:
        print('✅ Campo validation_metadata ya existe')