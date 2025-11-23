from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .auth import get_current_user
from .. import models, schemas

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=schemas.UserPreferenceOut)
def get_my_preferences(db: Session = Depends(get_db), user=Depends(get_current_user)):
    pref = db.query(models.UserPreference).filter_by(user_id=user.id).first()
    if not pref:
        return schemas.UserPreferenceOut(publication_type="all")
    if not pref.publication_type:
        pref.publication_type = "all"

    return schemas.UserPreferenceOut.model_validate(pref.__dict__)


@router.put("", response_model=schemas.UserPreferenceOut)
def upsert_my_preferences(
    payload: schemas.UserPreferenceIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    pref = db.query(models.UserPreference).filter_by(user_id=user.id).first()
    if not pref:
        pref = models.UserPreference(user_id=user.id)
        db.add(pref)
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "publication_type" and v not in ["all", "hotel", "actividad"]:
            continue
        setattr(pref, k, v)
    db.commit()
    db.refresh(pref)
    if not pref.publication_type:
        pref.publication_type = "all"
    return schemas.UserPreferenceOut.model_validate(pref.__dict__)
