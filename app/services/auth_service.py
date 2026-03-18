import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, MagicLinkToken
from app.config import settings
from app.exceptions import (
    InvalidTokenError,
    UserNotFoundError,
    UserAlreadyExistsError,
    AuthenticationError
)
from app.services.token_service import (
    generate_magic_link_token,
    verify_token,
    mark_token_used
)
from app.services.email_service import send_magic_link_email


async def create_magic_link_for_signup(
    db: AsyncSession,
    username: str,
    email: str
) -> bool:
    """
    Create magic link for user signup.

    Args:
        db: Database session
        username: Desired username
        email: User email address

    Returns:
        True if magic link created and email sent successfully

    Raises:
        UserAlreadyExistsError: If username or email already exists
    """
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == username)
    )
    if result.scalar_one_or_none():
        raise UserAlreadyExistsError("Username already taken")

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == email)
    )
    if result.scalar_one_or_none():
        raise UserAlreadyExistsError("Email already registered")

    # Generate magic link token (user_id=None for signup)
    token = await generate_magic_link_token(db, email, user_id=None, username=username)

    # Send email
    success = await send_magic_link_email(email, token, username)

    return success


async def create_magic_link_for_login(
    db: AsyncSession,
    email: str
) -> bool:
    """
    Create magic link for user login.

    Args:
        db: Database session
        email: User email address

    Returns:
        True if magic link created and email sent successfully

    Raises:
        UserNotFoundError: If user doesn't exist
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFoundError("No account found with this email")

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    # Generate magic link token with user_id
    token = await generate_magic_link_token(db, email, user_id=user.id)

    # Send email
    success = await send_magic_link_email(email, token, user.username)

    return success


async def create_magic_link_for_logout(
    db: AsyncSession,
    user: User
) -> bool:
    """
    Create magic link for user logout confirmation.

    Args:
        db: Database session
        user: User object requesting logout

    Returns:
        True if magic link created and email sent successfully
    """
    # Generate magic link token with user_id
    token = await generate_magic_link_token(db, user.email, user_id=user.id)

    # Send email with logout confirmation link
    success = await send_magic_link_email(
        user.email,
        token,
        user.username,
        action="logout"
    )

    return success


async def verify_magic_link(
    db: AsyncSession,
    token: str
) -> User:
    """
    Verify magic link and authenticate user.
    Handles both signup and login flows.

    Args:
        db: Database session
        token: Magic link token

    Returns:
        Authenticated User object

    Raises:
        InvalidTokenError: If token is invalid
    """
    # Verify token validity
    magic_link = await verify_token(db, token)

    # Check if this is a signup (user_id is None) or login flow
    if magic_link.user_id is None:
        # Signup flow - need to get username from token somehow
        # We'll need to store username in a separate field or get it from the request
        # For now, let's look for an existing token with the same email that might have username
        # Actually, we need to store username in the magic_link_tokens table for signup
        raise InvalidTokenError("Signup token format not supported yet")

    else:
        # Login flow - fetch existing user
        result = await db.execute(
            select(User).where(User.id == magic_link.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError("User account not found")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

    # Mark token as used
    await mark_token_used(db, token)

    return user


async def create_user_from_token(
    db: AsyncSession,
    token: str,
    username: str
) -> User:
    """
    Create a new user account from a signup magic link token.

    Args:
        db: Database session
        token: Magic link token
        username: Desired username

    Returns:
        Created User object

    Raises:
        InvalidTokenError: If token is invalid
    """
    # Verify token validity
    magic_link = await verify_token(db, token)

    # Verify this is a signup token (user_id should be None)
    if magic_link.user_id is not None:
        raise InvalidTokenError("This is not a signup token")

    # Check if username is still available
    result = await db.execute(
        select(User).where(User.username == username)
    )
    if result.scalar_one_or_none():
        raise UserAlreadyExistsError("Username already taken")

    # Create new user
    user = User(
        username=username,
        email=magic_link.email,
        last_login=datetime.utcnow()
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Mark token as used
    await mark_token_used(db, token)

    return user


def create_access_token(user_id: uuid.UUID) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User ID

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    to_encode = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID) -> str:
    """
    Create JWT refresh token.

    Args:
        user_id: User ID

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(
        days=settings.refresh_token_expire_days
    )

    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


async def verify_jwt_token(
    db: AsyncSession,
    token: str,
    token_type: str = "access"
) -> User:
    """
    Verify JWT token and return associated user.

    Args:
        db: Database session
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        User object

    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        user_id_str: str = payload.get("sub")
        payload_type: str = payload.get("type")

        if user_id_str is None or payload_type != token_type:
            raise AuthenticationError("Invalid token")

        user_id = uuid.UUID(user_id_str)

    except JWTError:
        raise AuthenticationError("Invalid token")

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundError("User not found")

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    return user
