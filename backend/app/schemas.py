from pydantic import BaseModel, EmailStr
try:
    from pydantic import ConfigDict
    _V2 = True
except Exception:
    _V2 = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    if _V2:
        # v2
        model_config = ConfigDict(from_attributes=True)
    else:
        # v1 fallback
        class Config:
            orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
