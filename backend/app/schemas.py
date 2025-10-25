from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional
from datetime import date, datetime

try:
    from pydantic import ConfigDict
    _V2 = True
except Exception:
    _V2 = False

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    security_question_1: str
    security_answer_1: str
    security_question_2: str
    security_answer_2: str

class UserLogin(BaseModel):
    identifier: str  #Puede ser username o email. Es algo generico que manda el front
    password: str

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | str | None = None 
    travel_preferences: str | None = None

    @validator('birth_date', pre=True)
    def parse_birth_date(cls, v):
        # Si el valor es un string vacío o nulo, lo convertimos en None
        if v == '' or v is None:
            return None
        # Si es un string (ej: "2002-05-02"), lo convertimos a un objeto date
        if isinstance(v, str):
            try:
                # El formato '%Y-%m-%d' debe coincidir con el del input HTML
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"'{v}' no es una fecha válida. Usar formato AAAA-MM-DD.")
        return v

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class RequestQuestions(BaseModel):
    identifier: str # Email o Username

class QuestionsOut(BaseModel):
    username: str
    security_question_1: str
    security_question_2: str

class VerifyAnswers(BaseModel):
    identifier: str
    security_answer_1: str
    security_answer_2: str

class ResetPasswordWithToken(BaseModel):
    new_password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None
    travel_preferences: str | None = None
    profile_picture_url: str | None = None
    role: str

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

class PublicationCreate(BaseModel):
    place_name: str = Field(..., min_length=2, max_length=200)
    country: str = Field(..., min_length=2, max_length=100)
    province: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=3, max_length=200)
    categories: Optional[List[str]] = None  # slugs

class PublicationOut(BaseModel):
    id: int
    place_name: str
    country: str
    province: str
    city: str
    address: str
    created_at: str
    photos: List[str] = []
    rating_avg: float = 0.0
    rating_count: int = 0
    categories: List[str] = []

    if _V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewOut(BaseModel):
    id: int
    rating: int
    comment: Optional[str] = None
    author_username: str
    created_at: str

    if _V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True