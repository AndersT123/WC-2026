import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Match(Base):
    """Match model for storing match information."""

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    home_team: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    away_team: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    match_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    venue: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",
        nullable=False,
        index=True
    )
    home_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    away_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
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
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="match",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, {self.home_team} vs {self.away_team}, status={self.status})>"
