import uuid
from typing import Optional
from datetime import datetime
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
