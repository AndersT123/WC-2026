import uuid
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.match import Match
from app.exceptions import MatchNotFoundError


async def get_all_matches(db: AsyncSession) -> List[Match]:
    """Fetch all matches ordered by match_datetime.

    Args:
        db: Database session

    Returns:
        List of Match objects ordered by datetime
    """
    result = await db.execute(
        select(Match).order_by(Match.match_datetime)
    )
    return result.scalars().all()


async def get_match_by_id(db: AsyncSession, match_id: uuid.UUID) -> Match:
    """Get a single match by ID.

    Args:
        db: Database session
        match_id: ID of the match

    Returns:
        The Match object

    Raises:
        MatchNotFoundError: If match doesn't exist
    """
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalars().first()
    if not match:
        raise MatchNotFoundError()
    return match


async def update_match_result(
    db: AsyncSession,
    match_id: uuid.UUID,
    home_score: int,
    away_score: int,
    status: str = "completed",
) -> Match:
    """Update match result and status.

    Args:
        db: Database session
        match_id: ID of the match
        home_score: Home team score
        away_score: Away team score
        status: Match status

    Returns:
        Updated Match object

    Raises:
        MatchNotFoundError: If match doesn't exist
    """
    match = await get_match_by_id(db, match_id)
    match.home_score = home_score
    match.away_score = away_score
    match.status = status
    match.updated_at = datetime.utcnow()
    db.add(match)
    await db.flush()
    await db.refresh(match)
    return match
