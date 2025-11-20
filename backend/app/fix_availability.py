#!/usr/bin/env python3
"""
Script para corregir los campos available_days y available_hours que están como diccionarios vacíos.
"""

from backend.app.db import SessionLocal
from backend.app.models import Publication

def fix_availability_fields():
    """Corrige los campos available_days y available_hours que están como diccionarios vacíos."""
    print("🔧 Corrigiendo campos de disponibilidad...")
    
    db = SessionLocal()
    try:
        pubs = db.query(Publication).all()
        fixed_count = 0
        
        for pub in pubs:
            needs_fix = False
            
            # Verificar available_days
            if pub.available_days == {} or pub.available_days is None:
                pub.available_days = []
                needs_fix = True
                print(f"  ✅ {pub.place_name}: available_days fijado")
            
            # Verificar available_hours  
            if pub.available_hours == {} or pub.available_hours is None:
                pub.available_hours = []
                needs_fix = True
                print(f"  ✅ {pub.place_name}: available_hours fijado")
            
            if needs_fix:
                fixed_count += 1
        
        db.commit()
        print(f"\n🎉 {fixed_count} publicaciones corregidas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_availability_fields()