from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..db import get_db
from .. import models, security, schemas
from ..models import User
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token faltante")
    token = authorization.split()[1]
    data = security.decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user_id = data.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido (no sub)")
        
    user = db.query(models.User).get(int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    hashed_answer_1 = security.hash_password(payload.security_answer_1)
    hashed_answer_2 = security.hash_password(payload.security_answer_2)

    user = models.User(
        email=payload.email,
        username=payload.username,
        hashed_password=security.hash_password(payload.password),
        first_name=getattr(payload, "first_name", None),
        last_name=getattr(payload, "last_name", None),
        birth_date=getattr(payload, "birth_date", None),
        travel_preferences=getattr(payload, "travel_preferences", None),
        security_question_1=payload.security_question_1,
        hashed_answer_1=hashed_answer_1,
        security_question_2=payload.security_question_2,
        hashed_answer_2=hashed_answer_2,
        role="user",  # 👈 nuevo
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
#Nuevo schema de userLogin con identifier generico
    user = db.query(models.User).filter(
        or_(models.User.email == payload.identifier, models.User.username == payload.identifier)
    ).first()

    #se busca al usuario por email o username primero para ver si se tiene que registrar o no
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no registrado. Por favor crea una cuenta."
        )

    #Si el usuario existe pero la contraseña es incorrecta, devolvemos un unauthorized
    if not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña o usuario incorrecta."
        )

    token_data = {"sub": str(user.id), "email": user.email, "username": user.username}
    token = security.create_access_token(token_data)
    
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.UserUpdate, # Recibe el nuevo esquema
    user: models.User = Depends(get_current_user), # Obtiene el usuario actual
    db: Session = Depends(get_db)
):
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.birth_date = payload.birth_date
    user.travel_preferences = payload.travel_preferences
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/change-password", response_model=dict)
def change_password(
    payload: schemas.PasswordUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not security.verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La contraseña actual es incorrecta."
        )

    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 8 caracteres."
        )

    user.hashed_password = security.hash_password(payload.new_password)
    
    db.add(user)
    db.commit()
    
    return {"message": "Contraseña actualizada con éxito"}

# PASO 1: El usuario pone su email/username y le devolvemos sus preguntas
@router.post("/forgot-password/get-questions", response_model=schemas.QuestionsOut)
def get_security_questions(payload: schemas.RequestQuestions, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        or_(models.User.email == payload.identifier, models.User.username == payload.identifier)
    ).first()

    if not user or not user.security_question_1:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no tiene preguntas configuradas.")
    
    return schemas.QuestionsOut(
        username=user.username,
        security_question_1=user.security_question_1,
        security_question_2=user.security_question_2
    )

# PASO 2: El usuario responde. Verificamos y le damos un token temporal
@router.post("/forgot-password/verify-answers", response_model=schemas.Token)
def verify_security_answers(payload: schemas.VerifyAnswers, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        or_(models.User.email == payload.identifier, models.User.username == payload.identifier)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Verificamos las respuestas hasheadas
    is_answer_1_correct = security.verify_password(payload.security_answer_1, user.hashed_answer_1)
    is_answer_2_correct = security.verify_password(payload.security_answer_2, user.hashed_answer_2)

    if not is_answer_1_correct or not is_answer_2_correct:
        raise HTTPException(status_code=401, detail="Una o ambas respuestas son incorrectas.")

    # Las respuestas son correctas. Generamos un token de 5 minutos.
    expires_delta = timedelta(minutes=5)
    token_data = {"sub": str(user.id), "scope": "password-reset-granted"}
    token = security.create_access_token(token_data, expires_delta=expires_delta)
    
    return {"access_token": token, "token_type": "bearer"}

# PASO 3: Con el token del Paso 2, el usuario crea la nueva contraseña
@router.post("/forgot-password/set-new-password", response_model=dict)
def set_new_password_with_token(
    payload: schemas.ResetPasswordWithToken,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    # (Esta lógica es la misma que teníamos en el flujo de email/código)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token faltante")
    token = authorization.split()[1]

    try:
        data = security.decode_token(token)
        if not data or data.get("scope") != "password-reset-granted":
            raise HTTPException(status_code=401, detail="Permiso denegado.")
        user_id = int(data["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres.")

    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    
    user.hashed_password = security.hash_password(payload.new_password)
    db.add(user)
    db.commit()
    
    return {"message": "Contraseña actualizada con éxito."}

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user
