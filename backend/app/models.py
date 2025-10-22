from sqlalchemy import Column, Integer, String, DateTime, func, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


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
    
class Publication(Base):
    __tablename__ = "publications"

    # columnas legacy
    name   = Column(String, nullable=True)     # legacy, la llenamos con place_name
    street = Column(String, nullable=True)     # legacy, la llenamos desde address
    number = Column(String, nullable=True)     # 🔹 NUEVA: legacy, la llenamos desde address

    id         = Column(Integer, primary_key=True, index=True)
    place_name = Column(String, nullable=False)
    country    = Column(String, nullable=False)
    province   = Column(String, nullable=False)
    city       = Column(String, nullable=False)
    address    = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),   # por si recreas/migras la tabla
        default=func.now(),          # <-- default del lado de SQLAlchemy (cliente)
    )

    photos = relationship(
        "PublicationPhoto",
        back_populates="publication",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class PublicationPhoto(Base):
    __tablename__ = "publication_photos"

    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(400), nullable=False)

    index_order = Column(Integer, nullable=False, server_default="0", default=0)

    publication = relationship("Publication", back_populates="photos")
