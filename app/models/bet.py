"""Betting models for moneyline bets."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class BetOutcome(str, Enum):
    """Possible bet outcomes."""
    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"


class BetStatus(str, Enum):
    """Bet status."""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    PUSH = "push"  # Draw when user bet on win/loss


class Bet(Base):
    """User bet on a match outcome."""
    __tablename__ = "bets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)

    # Bet details
    outcome = Column(SQLEnum(BetOutcome), nullable=False)  # What user is betting on
    odds = Column(Float, nullable=False)  # Odds at time of bet

    # Settlement
    status = Column(SQLEnum(BetStatus), default=BetStatus.PENDING, nullable=False)
    actual_payout = Column(Float, nullable=True)  # Actual winnings (if won)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    settled_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="bets")
    match = relationship("Match")

    # Unique constraint: one bet per match per user (applies to all leagues)
    __table_args__ = (
        UniqueConstraint('user_id', 'match_id', name='uq_user_match_bet'),
    )

    @property
    def tokens(self) -> int:
        """Always 1 token per bet."""
        return 1

    @property
    def potential_payout(self) -> float:
        """Calculate potential payout: 1 × odds."""
        return 1.0 * self.odds

    def __repr__(self):
        return f"<Bet {self.id}: {self.outcome} @ {self.odds} ({self.status})>"
