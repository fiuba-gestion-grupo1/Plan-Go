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

    id = Column(Integer, primary_key=True, index=True)
    place_name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    province = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

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

    publication = relationship("Publication", back_populates="photos")
