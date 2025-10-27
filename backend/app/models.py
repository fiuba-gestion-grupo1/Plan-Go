from sqlalchemy import Column, Integer, String, DateTime, func, Date, Text, ForeignKey, Table, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base
from sqlalchemy.types import JSON

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    travel_preferences = Column(Text, nullable=True)
    security_question_1 = Column(String, nullable=True)
    hashed_answer_1 = Column(String, nullable=True)
    security_question_2 = Column(String, nullable=True)
    hashed_answer_2 = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)
    role = Column(String(20), nullable=False, server_default="user", default="user", index=True)

# Asociación N–N
publication_categories = Table(
    "publication_categories",
    Base.metadata,
    Column("publication_id", Integer, ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, index=True, nullable=False)  # aventura|cultura|gastronomia
    name = Column(String(100), nullable=False)

class Publication(Base):
    __tablename__ = "publications"

    # legacy
    name   = Column(String, nullable=True)
    street = Column(String, nullable=True)
    number = Column(String, nullable=True)

    id         = Column(Integer, primary_key=True, index=True)
    place_name = Column(String, nullable=False)
    country    = Column(String, nullable=False)
    province   = Column(String, nullable=False)
    city       = Column(String, nullable=False)
    address    = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    # 🔹 NUEVOS CAMPOS que coinciden con UserPreference
    continent = Column(String, nullable=True)        # Ej: "américa", "europa"
    climate = Column(String, nullable=True)          # Ej: "templado", "tropical"
    activities = Column(JSON, nullable=True)         # Ej: ["playa", "gastronomía"]
    cost_per_day = Column(Float, nullable=True)      # Para comparar con budget_max
    duration_days = Column(Integer, nullable=True)   # Para comparar con duration_min/max

    # US-5.1
    rating_avg   = Column(Float,  nullable=False, server_default="0")
    rating_count = Column(Integer, nullable=False, server_default="0")

    photos = relationship("PublicationPhoto", back_populates="publication", cascade="all, delete-orphan", passive_deletes=True)

    # US-4.4
    categories = relationship("Category", secondary=publication_categories, backref="publications")

class PublicationPhoto(Base):
    __tablename__ = "publication_photos"
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(400), nullable=False)
    index_order = Column(Integer, nullable=False, server_default="0", default=0)
    publication = relationship("Publication", back_populates="photos")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating   = Column(Integer, nullable=False)  # 1..5
    comment  = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    publication = relationship("Publication", backref="reviews")
    author      = relationship("User")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    # Campos de preferencia que se podrian usar para buscar cuando implementemos IA
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    climates = Column(JSON, nullable=True)          # ["templado","frio","tropical"]
    activities = Column(JSON, nullable=True)        # ["playa","montaña","gastronomía"]
    continents = Column(JSON, nullable=True)        # ["europa","américa"]
    duration_min_days = Column(Integer, nullable=True)
    duration_max_days = Column(Integer, nullable=True)

    user = relationship("User", backref="preference", uselist=False)