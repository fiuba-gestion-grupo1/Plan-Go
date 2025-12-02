# backend/app/seed_user_content.py
from __future__ import annotations
from sqlalchemy.orm.collections import InstrumentedList

from sqlalchemy.orm import Session

try:
    from backend.app.db import SessionLocal, engine
    from backend.app import models
except ImportError:
    print("Error: Ejecutá este script como módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.seed_user_content")
    raise


def _get_user_preference(user) -> models.UserPreference | None:
    pref_rel = getattr(user, "preference", None)

    if pref_rel is None:
        return None

    # Si por la config del backref viene como lista (InstrumentedList)
    if isinstance(pref_rel, InstrumentedList) or isinstance(pref_rel, list):
        return pref_rel[0] if len(pref_rel) > 0 else None

    # Si ya viene como objeto
    return pref_rel


def _matches_preference(
    pref: models.UserPreference | None, pub: models.Publication
) -> bool:
    if not pref:
        return True

    if pref.continents and pub.continent:
        if pub.continent not in pref.continents:
            return False

    if pref.climates and pub.climate:
        if pub.climate not in pref.climates:
            return False

    if pref.activities and pub.activities:
        # pub.activities es JSON (list[str]) en tu modelo
        if not set(pref.activities).intersection(set(pub.activities)):
            return False

    return True


def _upsert_favorite(
    db: Session, user_id: int, publication_id: int, status: str = "pending"
) -> None:
    fav = (
        db.query(models.Favorite)
        .filter(
            models.Favorite.user_id == user_id,
            models.Favorite.publication_id == publication_id,
        )
        .first()
    )
    if fav:
        if fav.status != status:
            fav.status = status
            db.add(fav)
        return

    db.add(
        models.Favorite(
            user_id=user_id,
            publication_id=publication_id,
            status=status,
        )
    )


def seed_favorites(db: Session) -> None:
    # Por las dudas (si ya existe, no hace nada)
    models.Favorite.__table__.create(bind=engine, checkfirst=True)

    users = db.query(models.User).order_by(models.User.id.asc()).all()
    pubs = (
        db.query(models.Publication)
        .filter(models.Publication.status == "approved")
        .order_by(models.Publication.id.asc())
        .all()
    )

    if not users:
        print("⚠️ No hay usuarios. Corré seed_users primero.")
        return
    if not pubs:
        print("⚠️ No hay publicaciones. Corré seed_db/seed_benefits primero.")
        return

    for u in users:
        pref = _get_user_preference(u)

        pool = [p for p in pubs if _matches_preference(pref, p)]
        if len(pool) < 3:
            pool = pubs  # fallback si hay muy pocas coincidencias

        fav_count = 3 if u.role == "premium" else 2

        start_idx = u.id % len(pool)
        selected = [pool[(start_idx + k) % len(pool)] for k in range(fav_count)]

        for p in selected:
            _upsert_favorite(db, u.id, p.id, status="pending")

    db.commit()
    print("✅ Favoritos seedados/actualizados.")


def main():
    print("🚀 Iniciando seed de favoritos...")
    db = SessionLocal()
    try:
        seed_favorites(db)
    except Exception as e:
        print(f"❌ Error en seed_user_content: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
