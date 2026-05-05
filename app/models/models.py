from uuid6 import uuid7
from ..core.database import Base
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    TIMESTAMP,
    Boolean,
    Numeric,
    Integer,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import datetime


def current_time():
    """Returns the current UTC time."""
    return datetime.datetime.utcnow()


class Profile(Base):
    __tablename__ = "profile"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), nullable=False, unique=True, index=True)
    gender = Column(String(255), nullable=False, index=True)
    gender_probability = Column(Numeric(128), nullable=False)
    sample_size = Column(Integer, nullable=True)
    age = Column(Integer, nullable=False, index=True)
    age_group = Column(String(255), nullable=False, index=True)
    country_id = Column(String(255), nullable=False, index=True)
    country_name = Column(String(255), nullable=True)
    country_probability = Column(Numeric(128), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=current_time
    )


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    github_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    role = Column(String(50), nullable=False, default="analyst")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=current_time
    )

    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    token_hash = Column(String(512), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=current_time
    )

    user = relationship("User", back_populates="refresh_tokens")

    # updatedat = Column(
    #     TIMESTAMP(timezone=True),
    #     nullable=False,
    #     default=current_time,
    #     onupdate=current_time,
    # )
