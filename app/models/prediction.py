import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Prediction(Base):
    """Prediction model for storing user predictions."""

    __tablename__ = "predictions"

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
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    home_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    away_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    points_earned: Mapped[Optional[int]] = mapped_column(
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

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "match_id", name="uq_prediction"),
        CheckConstraint("home_score >= 0", name="ck_home_score_non_negative"),
        CheckConstraint("away_score >= 0", name="ck_away_score_non_negative"),
        Index("idx_user_match", "user_id", "match_id"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="predictions"
    )
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="predictions"
    )

    def __repr__(self) -> str:
        return f"<Prediction user_id={self.user_id} match_id={self.match_id} score={self.home_score}-{self.away_score}>"
