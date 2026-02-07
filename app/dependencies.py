from typing import Optional
import uuid
from fastapi import Depends, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.services.auth_service import verify_jwt_token
from app.models.user import User
from app.exceptions import AuthenticationError, NotLeagueMemberError, ForbiddenError
from app.services.league_service import verify_league_membership
from app.config import settings


async def get_db() -> AsyncSession:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency for getting the current authenticated user from JWT token in cookie.

    Args:
        access_token: JWT access token from httpOnly cookie
        db: Database session

    Returns:
        Current authenticated User

    Raises:
        AuthenticationError: If token is missing or invalid
    """
    if not access_token:
        raise AuthenticationError("Not authenticated")

    user = await verify_jwt_token(db, access_token, token_type="access")

    return user


async def get_current_user_optional(
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency for optionally getting the current user (doesn't raise on missing token).

    Args:
        access_token: JWT access token from httpOnly cookie
        db: Database session

    Returns:
        Current User if authenticated, None otherwise
    """
    if not access_token:
        return None

    try:
        user = await verify_jwt_token(db, access_token, token_type="access")
        return user
    except Exception:
        return None


async def get_current_user_league_member(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency for verifying user is a member of a league.

    Args:
        league_id: ID of the league
        user: Current authenticated user
        db: Database session

    Returns:
        Current User if they are a member of the league

    Raises:
        NotLeagueMemberError: If user is not a member of the league
    """
    is_member = await verify_league_membership(db, user.id, league_id)
    if not is_member:
        raise NotLeagueMemberError()
    return user


async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Dependency for verifying user is an admin.

    Args:
        user: Current authenticated user

    Returns:
        Current User if they are an admin

    Raises:
        ForbiddenError: If user is not an admin
    """
    if user.email not in settings.admin_emails:
        raise ForbiddenError("Admin access required")
    return user
