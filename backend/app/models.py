from sqlalchemy import (
    Column, Integer, String, DateTime, func, Date, Text,
    ForeignKey, Table, Float, UniqueConstraint, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from .db import Base


# ---------------------------
# User
# ---------------------------
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


# ---------------------------
# Categories (N-N)
# ---------------------------
publication_categories = Table(
    "publication_categories",
    Base.metadata,
    Column("publication_id", Integer, ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, index=True, nullable=False)  # ej: aventura|cultura|gastronomia
    name = Column(String(100), nullable=False)


# ---------------------------
# Publications
# ---------------------------
class Publication(Base):
    __tablename__ = "publications"

    # Legacy
    name   = Column(String, nullable=True)
    street = Column(String, nullable=True)
    number = Column(String, nullable=True)

    id         = Column(Integer, primary_key=True, index=True)
    place_name = Column(String, nullable=False)
    country    = Column(String, nullable=False)
    province   = Column(String, nullable=False)
    city       = Column(String, nullable=False)
    address    = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Workflow / autoría
    status = Column(String(20), nullable=False, server_default="approved", default="approved", index=True)
    rejection_reason = Column(Text, nullable=True)  # Razón de rechazo si status=rejected
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())

    # Enriquecimiento (opcionales)
    continent     = Column(String, nullable=True)   # ej: "américa", "europa"
    climate       = Column(String, nullable=True)   # ej: "templado", "tropical"
    activities    = Column(JSON, nullable=True)     # ej: ["playa", "gastronomía"]
    cost_per_day  = Column(Float, nullable=True)
    duration_min = Column(Integer, nullable=True)

    # Ratings (US-5.1)
    rating_avg   = Column(Float,  nullable=False, server_default="0")
    rating_count = Column(Integer, nullable=False, server_default="0")

    # Rels
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    photos = relationship(
        "PublicationPhoto",
        back_populates="publication",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    categories = relationship("Category", secondary=publication_categories, backref="publications")


class PublicationPhoto(Base):
    __tablename__ = "publication_photos"
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(400), nullable=False)
    index_order = Column(Integer, nullable=False, server_default="0", default=0)
    publication = relationship("Publication", back_populates="photos")

# Review Comments
# ---------------------------
class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    review = relationship("Review", back_populates="comments")
    author = relationship("User")

# ---------------------------
# Review Likes (N-N)
# ---------------------------
class ReviewLike(Base):
    __tablename__ = "review_likes"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    review = relationship("Review", back_populates="likes")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uq_review_like"),
    )

# ---------------------------
# Reviews
# ---------------------------
class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating   = Column(Integer, nullable=False)  # 1..5
    comment  = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, server_default="approved", default="approved", index=True)  # approved|under_review|hidden
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    publication = relationship("Publication", backref="reviews")
    author      = relationship("User")

    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan", passive_deletes=True)
    comments = relationship("ReviewComment", back_populates="review", cascade="all, delete-orphan", passive_deletes=True)


# ---------------------------
# Review Reports
# ---------------------------
class ReviewReport(Base):
    __tablename__ = "review_reports"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(100), nullable=False)  # spam, inappropriate, fake, etc.
    comments = Column(Text, nullable=True)  # Comentarios adicionales del usuario que reporta
    status = Column(String(20), nullable=False, server_default="pending", default="pending", index=True)  # pending|approved|rejected
    rejection_reason = Column(Text, nullable=True)  # Razón de rechazo si status=rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    review = relationship("Review")
    reporter = relationship("User")

    __table_args__ = (
        UniqueConstraint("review_id", "reporter_id", name="uq_review_report"),
    )


# ---------------------------
# User Preferences (1-1)
# ---------------------------
class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    climates   = Column(JSON, nullable=True)        # ["templado","frio","tropical"]
    activities = Column(JSON, nullable=True)        # ["playa","montaña","gastronomía"]
    continents = Column(JSON, nullable=True)        # ["europa","américa"]
    duration_min_days = Column(Integer, nullable=True)
    duration_max_days = Column(Integer, nullable=True)

    publication_type = Column(String(20), nullable=True, server_default="all", default="all") # all | hotel | actividad
    user = relationship("User", backref="preference", uselist=False)


# ---------------------------
# Favorites (UNIQUE user_id, publication_id)
# ---------------------------
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False, server_default="pending", default="pending")  
    
    user = relationship("User")
    publication = relationship("Publication")

    __table_args__ = (
        UniqueConstraint("user_id", "publication_id", name="uq_favorite_user_pub"),
    )


# ---------------------------
# Deletion Requests
# ---------------------------
class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, server_default="pending", default="pending", index=True)  # pending|approved|rejected
    reason = Column(Text, nullable=True)  # Motivo por el cual el usuario solicita la eliminación
    rejection_reason = Column(Text, nullable=True)  # Razón de rechazo si status=rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    publication = relationship("Publication")
    requested_by = relationship("User")


# ---------------------------
# Itineraries
# ---------------------------
class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget = Column(Integer, nullable=False)
    cant_persons = Column(Integer, nullable=False, server_default="1", default=1)
    trip_type = Column(String, nullable=False)
    arrival_time = Column(String, nullable=True)
    departure_time = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    generated_itinerary = Column(Text, nullable=True)
    publication_ids = Column(JSON, nullable=True)  # Lista de IDs de publicaciones utilizadas
    status = Column(String(20), nullable=False, server_default="pending", default="pending", index=True)  # pending|completed|failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="itineraries")


class SavedItinerary(Base):
    __tablename__ = "saved_itineraries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Usuario que guarda
    original_itinerary_id = Column(Integer, ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, index=True)  # Itinerario original
    destination = Column(String, nullable=False)  # Copia de los datos principales
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget = Column(Integer, nullable=False)
    cant_persons = Column(Integer, nullable=False)
    trip_type = Column(String, nullable=False)
    arrival_time = Column(String, nullable=True)
    departure_time = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    generated_itinerary = Column(Text, nullable=True)
    publication_ids = Column(JSON, nullable=True)
    original_author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Autor original
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], backref="saved_itineraries")
    original_itinerary = relationship("Itinerary", foreign_keys=[original_itinerary_id])
    original_author = relationship("User", foreign_keys=[original_author_id])


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invitee_email = Column(String, nullable=False, index=True)
    invitation_code = Column(String, unique=True, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    inviter = relationship("User", foreign_keys=[inviter_id], backref="sent_invitations")
    invited_user = relationship("User", foreign_keys=[invited_user_id])


class PremiumBenefit(Base):
    __tablename__ = "premium_benefits"

    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)  # "10% descuento en consumos"
    description = Column(Text, nullable=True)  # "Aplica en bebidas y comidas del menú principal"
    discount_percentage = Column(Integer, nullable=True)  # 10, 15, 20, etc.
    benefit_type = Column(String, nullable=False)  # "discount", "free_item", "upgrade", etc.
    terms_conditions = Column(Text, nullable=True)  # "Válido solo de lunes a viernes"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    publication = relationship("Publication", backref="premium_benefits")


class UserBenefit(Base):
    __tablename__ = "user_benefits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    benefit_id = Column(Integer, ForeignKey("premium_benefits.id", ondelete="CASCADE"), nullable=False, index=True)
    points_cost = Column(Integer, nullable=False)  # Puntos que costó el beneficio
    voucher_code = Column(String, unique=True, nullable=False, index=True)  # Código QR único
    is_used = Column(Boolean, default=False, nullable=False)  # Si ya fue utilizado
    obtained_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="obtained_benefits")
    benefit = relationship("PremiumBenefit")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    user = relationship("User", backref="expenses")
    trip = relationship("Trip", back_populates="expenses")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="trips")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    participants = relationship("TripParticipant", backref="trip", cascade="all, delete-orphan")

class TripParticipant(Base):
    __tablename__ = "trip_participants"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)



class TripInvitation(Base):
    __tablename__ = "trip_invitations"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invited_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, server_default="pending", default="pending")  # pending|accepted|rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invited_user = relationship("User", foreign_keys=[invited_user_id])
    invited_by_user = relationship("User", foreign_keys=[invited_by_user_id])
    trip = relationship("Trip", backref="invitations")


# ---------------------------
# Points System
# ---------------------------
class UserPoints(Base):
    """Tabla para el balance actual de puntos de cada usuario"""
    __tablename__ = "user_points"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    total_points = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", backref="points_balance")


class PointsTransaction(Base):
    """Tabla para el historial de movimientos de puntos"""
    __tablename__ = "points_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    points = Column(Integer, nullable=False)  # Positivo para ganar, negativo para gastar
    transaction_type = Column(String, nullable=False)  # 'review_earned', 'rating_earned', 'bonus', 'redeemed'
    description = Column(String, nullable=True)  # Descripción del movimiento
    reference_id = Column(Integer, nullable=True)  # ID de referencia (ej: review_id, publication_id)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="points_transactions")
