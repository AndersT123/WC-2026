import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class User(Base):
    """User model for storing user account information."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Relationship to magic link tokens
    magic_link_tokens: Mapped[List["MagicLinkToken"]] = relationship(
        "MagicLinkToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Relationships for leagues
    created_leagues: Mapped[List["League"]] = relationship(
        "League",
        foreign_keys="League.creator_id",
        back_populates="creator"
    )
    league_memberships: Mapped[List["LeagueMembership"]] = relationship(
        "LeagueMembership",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Relationships for betting
    bets: Mapped[List["Bet"]] = relationship(
        "Bet",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class MagicLinkToken(Base):
    """Magic link token model for passwordless authentication."""

    __tablename__ = "magic_link_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship to user
    user: Mapped["User"] = relationship(
        "User",
        back_populates="magic_link_tokens"
    )

    def __repr__(self) -> str:
        return f"<MagicLinkToken(id={self.id}, email={self.email}, used={self.used_at is not None})>"
