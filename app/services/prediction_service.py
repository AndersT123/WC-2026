import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.models.prediction import Prediction
from app.models.match import Match
from app.models.league import LeagueMembership
from app.exceptions import (
    NotLeagueMemberError,
    MatchAlreadyStartedError,
)


def get_outcome(home_score: int, away_score: int) -> str:
    """Determine match outcome.

    Args:
        home_score: Home team score
        away_score: Away team score

    Returns:
        "home_win", "away_win", or "draw"
    """
    if home_score > away_score:
        return "home_win"
    elif away_score > home_score:
        return "away_win"
    else:
        return "draw"


def calculate_witt_classic_points(
    predicted_home: int,
    predicted_away: int,
    actual_home: int,
    actual_away: int,
) -> int:
    """Calculate points for a prediction using Witt Classic scoring rules.

    Scoring rules:
    1. Correct Score (exact) → 5 points
    2. Correct winner/draw → 2 points
    3. Correct winner + 1 right score from either team → 3 points
    4. One right score, but wrong outcome → 1 point
    5. Else → 0 points

    Args:
        predicted_home: Predicted home team score
        predicted_away: Predicted away team score
        actual_home: Actual home team score
        actual_away: Actual away team score

    Returns:
        Points earned
    """
    # Exact score match
    if predicted_home == actual_home and predicted_away == actual_away:
        return 5

    # Determine outcomes
    predicted_outcome = get_outcome(predicted_home, predicted_away)
    actual_outcome = get_outcome(actual_home, actual_away)

    # Correct winner/draw
    if predicted_outcome == actual_outcome:
        # Correct winner + one exact score
        if predicted_home == actual_home or predicted_away == actual_away:
            return 3
        else:
            return 2

    # Wrong outcome but one score correct
    if predicted_home == actual_home or predicted_away == actual_away:
        return 1

    return 0


async def get_user_predictions_with_matches(
    db: AsyncSession,
    user_id: uuid.UUID,
    league_id: uuid.UUID,
) -> List[Prediction]:
    """Get user's predictions with match details (validates league membership).

    Args:
        db: Database session
        user_id: ID of the user
        league_id: ID of the league (used for membership validation only)

    Returns:
        List of Prediction objects with joined Match objects

    Raises:
        NotLeagueMemberError: If user is not a league member
    """
    # Validate user is in league
    result = await db.execute(
        select(LeagueMembership).where(
            (LeagueMembership.user_id == user_id)
            & (LeagueMembership.league_id == league_id)
        )
    )
    if not result.scalars().first():
        raise NotLeagueMemberError()

    # Return all user predictions (not filtered by league)
    result = await db.execute(
        select(Prediction)
        .options(joinedload(Prediction.match))
        .where(Prediction.user_id == user_id)
    )
    return result.unique().scalars().all()


async def upsert_prediction(
    db: AsyncSession,
    user_id: uuid.UUID,
    match_id: uuid.UUID,
    league_id: uuid.UUID,
    home_score: int,
    away_score: int,
) -> Prediction:
    """Create or update a prediction with validations.

    Args:
        db: Database session
        user_id: ID of the user
        match_id: ID of the match
        league_id: ID of the league
        home_score: Predicted home score
        away_score: Predicted away score

    Returns:
        Created or updated Prediction object

    Raises:
        NotLeagueMemberError: If user is not a league member
        MatchAlreadyStartedError: If match status is not "scheduled"
    """
    # Verify league membership
    result = await db.execute(
        select(LeagueMembership).where(
            (LeagueMembership.user_id == user_id)
            & (LeagueMembership.league_id == league_id)
        )
    )
    if not result.scalars().first():
        raise NotLeagueMemberError()

    # Check match status
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalars().first()
    if not match or match.status != "scheduled":
        raise MatchAlreadyStartedError()

    # Check if prediction exists
    result = await db.execute(
        select(Prediction).where(
            (Prediction.user_id == user_id)
            & (Prediction.match_id == match_id)
        )
    )
    prediction = result.scalars().first()

    if prediction:
        # Update existing
        prediction.home_score = home_score
        prediction.away_score = away_score
        db.add(prediction)
    else:
        # Create new
        prediction = Prediction(
            id=uuid.uuid4(),
            user_id=user_id,
            match_id=match_id,
            league_id=league_id,
            home_score=home_score,
            away_score=away_score,
        )
        db.add(prediction)

    await db.flush()
    return prediction


async def update_predictions_after_match(
    db: AsyncSession,
    match_id: uuid.UUID,
) -> int:
    """Calculate points for all predictions after a match finishes.

    Args:
        db: Database session
        match_id: ID of the match

    Returns:
        Number of predictions updated

    Raises:
        Exception: If match has no scores
    """
    # Get the match
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalars().first()
    if not match or match.home_score is None or match.away_score is None:
        raise Exception("Match does not have final scores")

    # Get all predictions for this match
    result = await db.execute(
        select(Prediction).where(Prediction.match_id == match_id)
    )
    predictions = result.scalars().all()

    # Update each prediction with calculated points
    updated_count = 0
    for prediction in predictions:
        points = calculate_witt_classic_points(
            prediction.home_score,
            prediction.away_score,
            match.home_score,
            match.away_score,
        )
        prediction.points_earned = points
        db.add(prediction)
        updated_count += 1

    await db.flush()
    return updated_count
