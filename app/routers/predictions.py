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
from app.schemas.match import MatchResultsResponse, MatchResultEntry, UserMatchResult
from app.models.match import Match
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


@router.get("/league/{league_id}/match-results", response_model=MatchResultsResponse)
async def get_match_results(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResultsResponse:
    """Get all completed matches with every league member's prediction and bet."""
    # Verify membership
    await get_current_user_league_member(league_id, user, db)

    # Get league
    league = await get_league_by_id(db, league_id)

    # Get league members
    members_result = await db.execute(
        select(User.id, User.username)
        .join(LeagueMembership, LeagueMembership.user_id == User.id)
        .where(LeagueMembership.league_id == league_id)
    )
    members = members_result.all()
    member_ids = [m.id for m in members]

    # Get completed matches sorted descending by datetime
    matches_result = await db.execute(
        select(Match)
        .where(Match.status == "completed")
        .order_by(Match.match_datetime.desc())
    )
    completed_matches = matches_result.scalars().all()

    match_entries = []
    for match in completed_matches:
        # Bulk fetch predictions for this match
        preds_result = await db.execute(
            select(Prediction)
            .where(and_(Prediction.match_id == match.id, Prediction.user_id.in_(member_ids)))
        )
        preds_by_user = {p.user_id: p for p in preds_result.scalars().all()}

        # Bulk fetch bets for this match
        bets_result = await db.execute(
            select(Bet)
            .where(and_(Bet.match_id == match.id, Bet.user_id.in_(member_ids)))
        )
        bets_by_user = {b.user_id: b for b in bets_result.scalars().all()}

        user_results = []
        for member in members:
            pred = preds_by_user.get(member.id)
            bet = bets_by_user.get(member.id)
            user_results.append(UserMatchResult(
                user_id=member.id,
                username=member.username,
                predicted_home=pred.home_score if pred else None,
                predicted_away=pred.away_score if pred else None,
                points_earned=float(pred.points_earned) if pred and pred.points_earned is not None else None,
                bet_outcome=bet.outcome.value if bet else None,
                bet_odds=bet.odds if bet else None,
                bet_status=bet.status.value if bet else None,
                bet_payout=bet.actual_payout if bet else None,
            ))

        match_entries.append(MatchResultEntry(
            match_id=match.id,
            home_team=match.home_team,
            away_team=match.away_team,
            match_datetime=match.match_datetime,
            home_score=match.home_score,
            away_score=match.away_score,
            user_results=user_results,
        ))

    return MatchResultsResponse(
        league_id=league_id,
        league_name=league.name,
        matches=match_entries,
    )
