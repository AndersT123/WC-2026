import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request model for creating/updating predictions."""

    match_id: uuid.UUID
    league_id: uuid.UUID
    home_score: int = Field(..., ge=0, description="Home team's predicted score")
    away_score: int = Field(..., ge=0, description="Away team's predicted score")


class PredictionResponse(BaseModel):
    """Response model for prediction data."""

    id: uuid.UUID
    user_id: uuid.UUID
    match_id: uuid.UUID
    home_score: int
    away_score: int
    points_earned: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
