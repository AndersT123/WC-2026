import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.schemas.match import MatchResponse, CreateMatchRequest, UpdateMatchResultRequest
from app.services.match_service import get_all_matches, get_match_by_id, create_match, update_match_result, delete_match
from app.services.prediction_service import update_predictions_after_match
from app.services.bet_service import settle_bets

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


@router.post("", response_model=MatchResponse, status_code=201)
async def create_match_endpoint(
    request: CreateMatchRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """
    Create a new future match.

    **Admin only endpoint.** Creates a new scheduled match.

    **Args:**
        request: CreateMatchRequest with team names, datetime, and optional venue

    **Returns:**
        MatchResponse with created match data (ID auto-generated)

    **Error Codes:**
        - 401 Unauthorized: User not authenticated
        - 403 Forbidden: User is not an admin
        - 422 Unprocessable Entity: Invalid request data (datetime not in future, empty team names, etc.)

    **Example:**
        POST /matches
        {
            "home_team": "Argentina",
            "away_team": "France",
            "match_datetime": "2026-06-14T18:00:00",
            "venue": "Berlin, Germany"
        }
    """
    logger.info(
        f"Admin {admin.email} creating match: {request.home_team} vs {request.away_team} "
        f"at {request.match_datetime}"
    )
    match = await create_match(
        db,
        request.home_team,
        request.away_team,
        request.match_datetime,
        request.venue,
    )
    await db.commit()
    await db.refresh(match)
    logger.info(f"Match {match.id} created successfully")
    return MatchResponse.model_validate(match)


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """Get a single match by ID."""
    match = await get_match_by_id(db, match_id)
    return MatchResponse.model_validate(match)


@router.delete("/{match_id}", status_code=204)
async def delete_match_endpoint(
    match_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a match and all associated predictions and bets. Admin only."""
    logger.info(f"Admin {admin.email} deleting match {match_id}")
    await delete_match(db, match_id)
    await db.commit()
    logger.info(f"Match {match_id} deleted successfully")


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

    # Settle all bets for this match
    try:
        settled_count = await settle_bets(
            db, match_id, request.home_score, request.away_score
        )
        logger.info(f"Settled {settled_count} bets for match {match_id}")
    except Exception as e:
        logger.error(
            f"Error settling bets for match {match_id}: {str(e)}",
            exc_info=True
        )

    await db.commit()
    await db.refresh(match)
    logger.info(f"Match {match_id} result updated successfully")
    return MatchResponse.model_validate(match)
