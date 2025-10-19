from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import shutil
import uuid
import os

from ..db import get_db
from .. import models, schemas
from .auth import get_current_user # Importamos la dependencia desde auth.py

router = APIRouter(prefix="/api/users", tags=["users"])

UPLOAD_DIR = "backend/app/static/uploads"

@router.put("/me/photo", response_model=schemas.UserOut)
def upload_profile_photo(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Tipo de archivo inválido. Solo se permiten JPG y PNG.")

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    relative_path = f"/static/uploads/{unique_filename}"
    user.profile_picture_url = relative_path
    db.add(user)
    db.commit()
    db.refresh(user)

    return user