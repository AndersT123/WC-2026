import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CreateLeagueRequest(BaseModel):
    """Request model for creating a league."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class JoinLeagueRequest(BaseModel):
    """Request model for joining a league."""

    code: str = Field(..., min_length=8, max_length=8)


class LeagueResponse(BaseModel):
    """Response model for league data."""

    id: uuid.UUID
    name: str
    code: str
    creator_id: uuid.UUID
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeagueWithMemberCount(LeagueResponse):
    """League response with member count."""

    member_count: int = 0


class LeaderboardEntry(BaseModel):
    """Leaderboard entry for a user in a league."""

    user_id: uuid.UUID
    username: str
    total_points: float
    rank: int


class CombinedLeaderboardEntry(BaseModel):
    """Combined leaderboard entry with both predictions and betting scores."""

    user_id: uuid.UUID
    username: str
    rank: int

    # Combined total
    total_score: float

    # Individual scores
    predictions_score: float  # Witt's Classic points
    betting_score: float      # Total betting payouts


class LeaderboardResponse(BaseModel):
    """Response model for league leaderboard."""

    league_id: uuid.UUID
    league_name: str
    entries: List[LeaderboardEntry]


class CombinedLeaderboardResponse(BaseModel):
    """Response model for combined leaderboard (predictions + betting)."""

    league_id: uuid.UUID
    league_name: str
    entries: List[CombinedLeaderboardEntry]
