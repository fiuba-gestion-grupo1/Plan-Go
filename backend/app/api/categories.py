from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from ..db import get_db
from .. import models
from .auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    """
    Devuelve todos los slugs de categorías existentes (orden alfabético).
    """
    rows = db.execute(text("SELECT slug FROM categories ORDER BY slug COLLATE NOCASE ASC")).fetchall()
    return [r[0] for r in rows]

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not (current_user.role == "admin" or current_user.username == "admin"):
        raise HTTPException(status_code=403, detail="Solo administradores")
    return current_user

@router.post("/seed")
def seed_categories(payload: dict, 
                    db: Session = Depends(get_db), 
                    _: models.User = Depends(require_admin)):
    """
    Crea categorías por slugs (ignora duplicados).
    Body: {"slugs": ["aventura","cultura","gastronomia"]}
    """
    slugs = payload.get("slugs", []) or []
    inserted = 0
    for s in slugs:
        s = (s or "").strip().lower()
        if not s:
            continue
        db.execute(text("INSERT OR IGNORE INTO categories (slug) VALUES (:slug)"), {"slug": s})
        inserted += 1
    db.commit()
    return {"ok": True, "inserted": inserted, "count_submitted": len(slugs)}
