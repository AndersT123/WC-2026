import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class League(Base):
    """League model for managing prediction leagues."""

    __tablename__ = "leagues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    code: Mapped[str] = mapped_column(
        String(8),
        unique=True,
        nullable=False,
        index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
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

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_leagues"
    )
    members: Mapped[List["LeagueMembership"]] = relationship(
        "LeagueMembership",
        back_populates="league",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<League(id={self.id}, name={self.name}, code={self.code})>"


class LeagueMembership(Base):
    """LeagueMembership model for tracking league membership and roles."""

    __tablename__ = "league_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="member",
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "league_id", name="uq_user_league"),
        Index("idx_league_user", "league_id", "user_id"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="league_memberships"
    )
    league: Mapped["League"] = relationship(
        "League",
        back_populates="members"
    )

    def __repr__(self) -> str:
        return f"<LeagueMembership(user_id={self.user_id}, league_id={self.league_id}, role={self.role})>"
