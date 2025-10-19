from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..db import get_db
from .. import models, security, schemas


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
    user = models.User(username=payload.username, email=payload.email, hashed_password=security.hash_password(payload.password))
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


#@router.get("/me", response_model=schemas.UserOut)
#def me(
#    authorization: str | None = Header(default=None),
#    db: Session = Depends(get_db)
#):
#    if not authorization or not authorization.lower().startswith("bearer "):
#        raise HTTPException(status_code=401, detail="Token faltante")
#    token = authorization.split()[1]
#    data = security.decode_token(token)
#    if not data:
#        raise HTTPException(status_code=401, detail="Token inválido")
#    user = db.query(models.User).get(int(data["sub"]))
#    if not user:
#        raise HTTPException(status_code=404, detail="Usuario no encontrado")
#    return user
