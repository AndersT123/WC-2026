import uuid
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class MatchResponse(BaseModel):
    """Response model for match data."""

    id: uuid.UUID
    home_team: str
    away_team: str
    match_datetime: datetime
    venue: Optional[str]
    status: str
    home_score: Optional[int]
    away_score: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchWithPrediction(MatchResponse):
    """Response model for match with user's prediction."""

    user_prediction: Optional["PredictionResponse"] = None

    model_config = {"from_attributes": True}


class CreateMatchRequest(BaseModel):
    """Request model for creating a new match."""

    home_team: str = Field(..., min_length=1, max_length=100)
    away_team: str = Field(..., min_length=1, max_length=100)
    match_datetime: datetime
    venue: Optional[str] = Field(None, max_length=200)

    @field_validator('home_team', 'away_team')
    @classmethod
    def validate_teams(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError('Team name cannot be empty')
        return v.strip()

    @field_validator('match_datetime')
    @classmethod
    def validate_datetime(cls, v: datetime) -> datetime:
        # Get current time in UTC, handling both naive and aware datetimes
        now = datetime.now(timezone.utc)
        # Make v aware if it's naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError('Match datetime must be in the future')
        return v


class UpdateMatchResultRequest(BaseModel):
    """Request model for updating match result."""

    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    status: str = Field(default="completed")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ['scheduled', 'in_progress', 'completed', 'cancelled']
        if v not in allowed:
            raise ValueError(f'Status must be one of: {", ".join(allowed)}')
        return v


from app.schemas.prediction import PredictionResponse

MatchWithPrediction.model_rebuild()
