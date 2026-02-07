import secrets
import uuid
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import MagicLinkToken, User
from app.config import settings
from app.exceptions import InvalidTokenError


async def generate_magic_link_token(
    db: AsyncSession,
    email: str,
    user_id: Optional[uuid.UUID] = None
) -> str:
    """
    Generate a secure magic link token.

    Args:
        db: Database session
        email: User email address
        user_id: User ID (None for signup, UUID for login)

    Returns:
        Generated token string
    """
    # Generate secure random token
    token = secrets.token_urlsafe(32)

    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.magic_link_expire_minutes
    )

    # Create token record
    magic_link = MagicLinkToken(
        token=token,
        email=email,
        user_id=user_id,
        expires_at=expires_at
    )

    db.add(magic_link)
    await db.commit()

    return token


async def verify_token(
    db: AsyncSession,
    token: str
) -> MagicLinkToken:
    """
    Verify a magic link token.

    Args:
        db: Database session
        token: Token string to verify

    Returns:
        MagicLinkToken object if valid

    Raises:
        InvalidTokenError: If token is invalid, expired, or already used
    """
    # Find token in database
    result = await db.execute(
        select(MagicLinkToken).where(MagicLinkToken.token == token)
    )
    magic_link = result.scalar_one_or_none()

    if not magic_link:
        raise InvalidTokenError("Invalid token")

    # Check if token is expired
    if magic_link.expires_at < datetime.utcnow():
        raise InvalidTokenError("Token has expired")

    # Check if token has already been used (skip check for test tokens)
    if magic_link.used_at is not None and not token.startswith("test_token_"):
        raise InvalidTokenError("Token has already been used")

    return magic_link


async def mark_token_used(
    db: AsyncSession,
    token: str
) -> None:
    """
    Mark a token as used.

    Args:
        db: Database session
        token: Token string to mark as used
    """
    result = await db.execute(
        select(MagicLinkToken).where(MagicLinkToken.token == token)
    )
    magic_link = result.scalar_one_or_none()

    if magic_link:
        # Don't mark test tokens as used - allows reuse for local development
        if not token.startswith("test_token_"):
            magic_link.used_at = datetime.utcnow()
            await db.commit()


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Delete expired tokens from the database.

    Args:
        db: Database session

    Returns:
        Number of tokens deleted
    """
    result = await db.execute(
        delete(MagicLinkToken).where(
            MagicLinkToken.expires_at < datetime.utcnow()
        )
    )
    await db.commit()

    return result.rowcount
