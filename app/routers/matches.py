import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.schemas.match import MatchResponse, UpdateMatchResultRequest
from app.services.match_service import get_all_matches, get_match_by_id, update_match_result
from app.services.prediction_service import update_predictions_after_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=List[MatchResponse])
async def list_matches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MatchResponse]:
    """Get all matches."""
    matches = await get_all_matches(db)
    return [MatchResponse.model_validate(m) for m in matches]


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """Get a single match by ID."""
    match = await get_match_by_id(db, match_id)
    return MatchResponse.model_validate(match)


@router.put("/{match_id}/result", response_model=MatchResponse)
async def update_match_result_endpoint(
    match_id: uuid.UUID,
    request: UpdateMatchResultRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """
    Update match result and automatically calculate prediction points.

    **Admin only endpoint.** Updates the match scores and status, then automatically
    calculates and awards points to all predictions for this match using the Witt Classic
    scoring system.

    **Scoring Rules:**
    - Exact score: 5 points
    - Correct winner + 1 right score: 3 points
    - Correct winner/draw: 2 points
    - One right score but wrong outcome: 1 point
    - Otherwise: 0 points

    **Args:**
        match_id: UUID of the match to update
        request: UpdateMatchResultRequest with home_score, away_score, and status

    **Returns:**
        MatchResponse with updated match data

    **Error Codes:**
        - 401 Unauthorized: User not authenticated
        - 403 Forbidden: User is not an admin
        - 404 Not Found: Match does not exist
        - 422 Unprocessable Entity: Invalid request data (negative scores or invalid status)

    **Example:**
        PUT /matches/123e4567-e89b-12d3-a456-426614174000/result
        {
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
    """
    # Update match
    logger.info(
        f"Admin {admin.email} updating match {match_id}: "
        f"{request.home_score}-{request.away_score}, status={request.status}"
    )
    match = await update_match_result(
        db, match_id, request.home_score, request.away_score, request.status
    )

    # Calculate points for all predictions
    try:
        updated_count = await update_predictions_after_match(db, match_id)
        logger.info(f"Updated {updated_count} predictions for match {match_id}")
    except Exception as e:
        logger.error(
            f"Error updating predictions for match {match_id}: {str(e)}",
            exc_info=True
        )

    await db.commit()
    await db.refresh(match)
    logger.info(f"Match {match_id} result updated successfully")
    return MatchResponse.model_validate(match)
