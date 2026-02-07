"""Schemas for betting."""

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List


class BetOutcomeOdds(BaseModel):
    """Odds for a specific bet outcome."""
    outcome: str  # "home_win", "draw", "away_win"
    odds: float
    implied_probability: float  # Implied probability from odds


class MatchOdds(BaseModel):
    """Odds for a match."""
    match_id: uuid.UUID
    home_team: str
    away_team: str
    match_datetime: datetime
    outcomes: List[BetOutcomeOdds]

    model_config = {"from_attributes": True}


class PlaceBetRequest(BaseModel):
    """Request to place a bet."""
    match_id: uuid.UUID
    outcome: str  # "home_win", "draw", "away_win"


class BetResponse(BaseModel):
    """Response with bet details."""
    id: uuid.UUID
    user_id: uuid.UUID
    match_id: uuid.UUID
    outcome: str
    tokens: int = 3
    odds: float
    potential_payout: float
    status: str
    actual_payout: Optional[float]
    created_at: datetime
    settled_at: Optional[datetime]

    @classmethod
    def model_validate(cls, bet):
        """Custom validation to compute potential_payout."""
        return cls(
            id=bet.id,
            user_id=bet.user_id,
            match_id=bet.match_id,
            outcome=bet.outcome,
            tokens=3,
            odds=bet.odds,
            potential_payout=3.0 * bet.odds,
            status=bet.status.value,
            actual_payout=bet.actual_payout,
            created_at=bet.created_at,
            settled_at=bet.settled_at
        )

    model_config = {"from_attributes": True}


class BetHistoryResponse(BaseModel):
    """Bet with match details."""
    id: uuid.UUID
    match_id: uuid.UUID
    home_team: str
    away_team: str
    outcome: str  # What user bet on
    tokens: int = 3
    odds: float
    potential_payout: float
    status: str  # pending, won, lost, push
    actual_payout: Optional[float]
    match_datetime: datetime
    created_at: datetime
    settled_at: Optional[datetime]

    model_config = {"from_attributes": True}
