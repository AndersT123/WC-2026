import string
import random
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.models.league import League, LeagueMembership
from app.models.user import User
from app.exceptions import LeagueNotFoundError, AlreadyLeagueMemberError


async def generate_unique_league_code(db: AsyncSession, max_retries: int = 5) -> str:
    """Generate a unique 8-character uppercase alphanumeric league code.

    Args:
        db: Database session
        max_retries: Maximum number of retries to generate a unique code

    Returns:
        A unique 8-character code

    Raises:
        Exception: If unable to generate a unique code after max_retries
    """
    chars = string.ascii_uppercase + string.digits
    for _ in range(max_retries):
        code = "".join(random.choices(chars, k=8))

        # Check if code already exists
        result = await db.execute(
            select(League).where(League.code == code)
        )
        if result.scalars().first() is None:
            return code

    raise Exception("Failed to generate unique league code after retries")


async def create_league(
    db: AsyncSession,
    name: str,
    creator_id: uuid.UUID,
    description: str = None,
) -> League:
    """Create a new league and auto-join the creator.

    Args:
        db: Database session
        name: League name
        creator_id: ID of the user creating the league
        description: Optional league description

    Returns:
        Created League object
    """
    # Generate unique code
    code = await generate_unique_league_code(db)

    # Create league
    league = League(
        id=uuid.uuid4(),
        name=name,
        code=code,
        creator_id=creator_id,
        description=description,
        is_active=True,
    )
    db.add(league)
    await db.flush()

    # Auto-join creator as "creator" role
    membership = LeagueMembership(
        id=uuid.uuid4(),
        user_id=creator_id,
        league_id=league.id,
        role="creator",
    )
    db.add(membership)
    await db.flush()

    return league


async def join_league(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
) -> League:
    """Join a league with code.

    Args:
        db: Database session
        user_id: ID of the user joining
        code: League code

    Returns:
        The League object

    Raises:
        LeagueNotFoundError: If league code doesn't exist
        AlreadyLeagueMemberError: If user is already a member
    """
    # Find league by code
    result = await db.execute(
        select(League).where(League.code == code)
    )
    league = result.scalars().first()
    if not league:
        raise LeagueNotFoundError(f"League with code '{code}' not found")

    # Check if already a member
    result = await db.execute(
        select(LeagueMembership).where(
            (LeagueMembership.user_id == user_id)
            & (LeagueMembership.league_id == league.id)
        )
    )
    if result.scalars().first():
        raise AlreadyLeagueMemberError()

    # Create membership
    membership = LeagueMembership(
        id=uuid.uuid4(),
        user_id=user_id,
        league_id=league.id,
        role="member",
    )
    db.add(membership)
    await db.flush()

    return league


async def get_user_leagues(db: AsyncSession, user_id: uuid.UUID) -> List[League]:
    """Get all leagues a user is a member of.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of League objects
    """
    result = await db.execute(
        select(League)
        .join(LeagueMembership)
        .where(LeagueMembership.user_id == user_id)
    )
    return result.scalars().all()


async def get_league_by_id(db: AsyncSession, league_id: uuid.UUID) -> League:
    """Get a league by ID.

    Args:
        db: Database session
        league_id: ID of the league

    Returns:
        The League object

    Raises:
        LeagueNotFoundError: If league doesn't exist
    """
    result = await db.execute(
        select(League).where(League.id == league_id)
    )
    league = result.scalars().first()
    if not league:
        raise LeagueNotFoundError()
    return league


async def verify_league_membership(
    db: AsyncSession,
    user_id: uuid.UUID,
    league_id: uuid.UUID,
) -> bool:
    """Verify if a user is a member of a league.

    Args:
        db: Database session
        user_id: ID of the user
        league_id: ID of the league

    Returns:
        True if user is a member, False otherwise
    """
    result = await db.execute(
        select(LeagueMembership).where(
            (LeagueMembership.user_id == user_id)
            & (LeagueMembership.league_id == league_id)
        )
    )
    return result.scalars().first() is not None


async def get_league_member_count(db: AsyncSession, league_id: uuid.UUID) -> int:
    """Get the number of members in a league.

    Args:
        db: Database session
        league_id: ID of the league

    Returns:
        Number of members
    """
    result = await db.execute(
        select(func.count(LeagueMembership.id)).where(
            LeagueMembership.league_id == league_id
        )
    )
    return result.scalar() or 0
