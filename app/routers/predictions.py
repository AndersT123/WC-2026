import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.dependencies import get_db, get_current_user, get_current_user_league_member
from app.models.user import User
from app.models.prediction import Prediction
from app.models.league import LeagueMembership
from app.models.bet import Bet
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.schemas.league import (
    LeaderboardResponse,
    LeaderboardEntry,
    CombinedLeaderboardEntry,
    CombinedLeaderboardResponse
)
from app.services.prediction_service import upsert_prediction, get_user_predictions_with_matches
from app.services.league_service import get_league_by_id

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_prediction(
    request: PredictionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    """Create or update a prediction (upsert logic)."""
    prediction = await upsert_prediction(
        db,
        user.id,
        request.match_id,
        request.league_id,
        request.home_score,
        request.away_score,
    )
    await db.commit()
    await db.refresh(prediction)
    return PredictionResponse.model_validate(prediction)


@router.get("/league/{league_id}/me", response_model=List[PredictionResponse])
async def get_my_predictions(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PredictionResponse]:
    """Get current user's predictions for a league."""
    # Verify membership
    league_member = await get_current_user_league_member(league_id, user, db)

    predictions = await get_user_predictions_with_matches(db, user.id, league_id)
    return [PredictionResponse.model_validate(p) for p in predictions]


@router.get("/league/{league_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    """Get league leaderboard (must be a member)."""
    # Verify membership
    league_member = await get_current_user_league_member(league_id, user, db)

    # Get league
    league = await get_league_by_id(db, league_id)

    # Get all users in league
    members_result = await db.execute(
        select(User.id, User.username)
        .join(LeagueMembership, LeagueMembership.user_id == User.id)
        .where(LeagueMembership.league_id == league_id)
    )
    members = members_result.all()

    # Build leaderboard entries with both prediction points and bet payouts
    entries = []
    for user_id, username in members:
        pred_result = await db.execute(
            select(func.sum(Prediction.points_earned))
            .where(Prediction.user_id == user_id)
        )
        pred_score = pred_result.scalar() or 0.0

        bet_result = await db.execute(
            select(func.sum(Bet.actual_payout))
            .where(Bet.user_id == user_id)
            .where(Bet.status.in_(["won", "lost", "push"]))
        )
        bet_score = bet_result.scalar() or 0.0

        total_points = float(pred_score) + float(bet_score)
        entries.append(
            LeaderboardEntry(
                user_id=user_id,
                username=username,
                total_points=total_points,
                rank=0,  # Will be set after sorting
            )
        )

    # Sort by total_points descending and assign ranks
    entries.sort(key=lambda e: e.total_points, reverse=True)
    for rank, entry in enumerate(entries, 1):
        entry.rank = rank

    return LeaderboardResponse(
        league_id=league_id,
        league_name=league.name,
        entries=entries,
    )


@router.get("/league/{league_id}/combined-leaderboard", response_model=CombinedLeaderboardResponse)
async def get_combined_leaderboard(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CombinedLeaderboardResponse:
    """Get combined leaderboard with both Witt's Classic predictions and betting scores."""
    # Verify membership
    league_member = await get_current_user_league_member(league_id, user, db)

    # Get league
    league = await get_league_by_id(db, league_id)

    # Get all users in league
    members_result = await db.execute(
        select(User.id, User.username)
        .join(LeagueMembership, LeagueMembership.user_id == User.id)
        .where(LeagueMembership.league_id == league_id)
    )
    members = members_result.all()

    entries = []

    for user_id, username in members:
        # Get predictions score (Witt's Classic)
        predictions_result = await db.execute(
            select(func.sum(Prediction.points_earned))
            .where(Prediction.user_id == user_id)
        )
        predictions_score = predictions_result.scalar() or 0.0

        # Get betting score (sum of actual payouts for all settled bets)
        # Note: Bets now apply to all leagues, not league-specific
        bets_result = await db.execute(
            select(func.sum(Bet.actual_payout))
            .where(Bet.user_id == user_id)
            .where(Bet.status.in_(["won", "lost", "push"]))  # Only settled bets
        )
        betting_score = bets_result.scalar() or 0.0

        # Combine scores
        total_score = float(predictions_score) + float(betting_score)

        entries.append(
            CombinedLeaderboardEntry(
                user_id=user_id,
                username=username,
                rank=0,  # Will be set after sorting
                total_score=total_score,
                predictions_score=float(predictions_score),
                betting_score=float(betting_score),
            )
        )

    # Sort by total score descending
    entries.sort(key=lambda e: e.total_score, reverse=True)

    # Add ranks
    for rank, entry in enumerate(entries, 1):
        entry.rank = rank

    return CombinedLeaderboardResponse(
        league_id=league_id,
        league_name=league.name,
        entries=entries,
    )
