from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional
from datetime import date, datetime

# Compatibilidad Pydantic v1/v2
try:
    from pydantic import ConfigDict
    _V2 = True
except Exception:  # pragma: no cover
    _V2 = False


# -------------------------------------------------
# Auth / Users
# -------------------------------------------------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    security_question_1: str
    security_answer_1: str
    security_question_2: str
    security_answer_2: str


class UserLogin(BaseModel):
    # Puede ser username o email
    identifier: str
    password: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | str | None = None
    travel_preferences: str | None = None

    @validator("birth_date", pre=True)
    def parse_birth_date(cls, v):
        # Acepta "", None, "YYYY-MM-DD" o date
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"'{v}' no es una fecha válida. Usar formato AAAA-MM-DD.")
        return v


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class RequestQuestions(BaseModel):
    identifier: str  # Email o Username


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
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -------------------------------------------------
# Publications
# -------------------------------------------------
class PublicationCreate(BaseModel):
    place_name: str = Field(..., min_length=2, max_length=200)
    country: str = Field(..., min_length=2, max_length=100)
    province: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=3, max_length=200)
    # Para endpoints JSON (si se usan). En multipart llega como CSV y se parsea en el router.
    categories: Optional[List[str]] = None  # slugs


class PublicationOut(BaseModel):
    id: int
    place_name: str
    country: str
    province: str
    city: str
    address: str
    status: str = "approved"
    created_by_user_id: int | None = None
    created_at: str
    photos: List[str] = []

    # Enriquecimiento / ratings / taxonomía
    rating_avg: float = 0.0
    rating_count: int = 0
    categories: List[str] = []

    # Flags opcionales que algunos endpoints setean
    is_favorite: bool = False
    has_pending_deletion: bool = False

    if _V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


# -------------------------------------------------
# Reviews
# -------------------------------------------------
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


# -------------------------------------------------
# User Preferences (IA / filtros futuros)
# -------------------------------------------------
class UserPreferenceIn(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    climates: Optional[List[str]] = None
    activities: Optional[List[str]] = None
    continents: Optional[List[str]] = None
    duration_min_days: Optional[int] = None
    duration_max_days: Optional[int] = None


class UserPreferenceOut(UserPreferenceIn):
    # Por ahora la salida es igual a la entrada
    pass


# -------------------------------------------------
# Deletion Requests (admin)
# -------------------------------------------------
class DeletionRequestOut(BaseModel):
    id: int
    publication_id: int
    requested_by_user_id: int
    status: str
    created_at: str
    publication: PublicationOut

    if _V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True
