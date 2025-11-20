# backend/app/reset_publications.py
"""
Script para limpiar y recargar solo las publicaciones y datos relacionados
"""

try:
    from backend.app.db import SessionLocal
    from backend.app import models
except ImportError:
    print("Error: Ejecuta este script como un módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.reset_publications")
    exit(1)


def reset_publications_data():
    """
    Elimina todas las publicaciones, fotos, reseñas, favoritos y datos relacionados.
    Mantiene usuarios y otros datos del sistema.
    """
    print("🗑️  Iniciando limpieza de publicaciones...")
    
    db = SessionLocal()
    try:
        # 1. Eliminar reseñas (deben ir primero por foreign keys)
        review_count = db.query(models.Review).count()
        if review_count > 0:
            db.query(models.Review).delete()
            print(f"   ✅ Eliminadas {review_count} reseñas")

        # 2. Eliminar comentarios de reseñas
        comment_count = db.query(models.ReviewComment).count()
        if comment_count > 0:
            db.query(models.ReviewComment).delete()
            print(f"   ✅ Eliminados {comment_count} comentarios")

        # 3. Eliminar favoritos
        favorite_count = db.query(models.Favorite).count()
        if favorite_count > 0:
            db.query(models.Favorite).delete()
            print(f"   ✅ Eliminados {favorite_count} favoritos")

        # 4. Eliminar fotos de publicaciones
        photo_count = db.query(models.PublicationPhoto).count()
        if photo_count > 0:
            db.query(models.PublicationPhoto).delete()
            print(f"   ✅ Eliminadas {photo_count} fotos")

        # 5. Eliminar solicitudes de eliminación
        try:
            deletion_count = db.query(models.DeletionRequest).count()
            if deletion_count > 0:
                db.query(models.DeletionRequest).delete()
                print(f"   ✅ Eliminadas {deletion_count} solicitudes de eliminación")
        except Exception:
            print("   ⚠️  Tabla deletion_requests no existe o ya está vacía")

        # 6. Eliminar publicaciones
        pub_count = db.query(models.Publication).count()
        if pub_count > 0:
            db.query(models.Publication).delete()
            print(f"   ✅ Eliminadas {pub_count} publicaciones")

        # 7. Resetear IDs de autoincremento (solo para SQLite)
        try:
            db.execute("DELETE FROM sqlite_sequence WHERE name IN ('publications', 'reviews', 'publication_photos', 'favorites')")
            print("   ✅ IDs de autoincremento reseteados")
        except Exception:
            print("   ⚠️  No se pudieron resetear los IDs (puede ser normal en PostgreSQL)")

        db.commit()
        print("✅ Limpieza completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reload_publications():
    """
    Recarga las publicaciones ejecutando el script de seed
    """
    print("🌱 Recargando publicaciones desde seeds...")
    
    try:
        # Importar y ejecutar la función de seed
        from backend.app.seed_db import seed_publications
        
        db = SessionLocal()
        try:
            seed_publications(db)
            print("✅ Publicaciones recargadas exitosamente")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error recargando publicaciones: {e}")
        raise


if __name__ == "__main__":
    print("🔄 RESET Y RECARGA DE PUBLICACIONES")
    print("=" * 50)
    
    try:
        # Paso 1: Limpiar datos existentes
        reset_publications_data()
        
        print()
        
        # Paso 2: Recargar desde seeds
        reload_publications()
        
        print()
        print("🎉 Proceso completado exitosamente!")
        print("📝 Las publicaciones han sido actualizadas con los datos más recientes del seed.")
        
    except Exception as e:
        print(f"💥 El proceso falló: {e}")
        exit(1)