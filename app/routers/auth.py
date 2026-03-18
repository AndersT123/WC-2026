from typing import Optional, Union
from fastapi import APIRouter, Depends, Response, Cookie, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.dependencies import get_db, get_current_user
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    MagicLinkResponse,
    VerifyResponse,
    RefreshResponse,
    LogoutResponse,
    UserResponse
)
from app.services.auth_service import (
    create_magic_link_for_signup,
    create_magic_link_for_login,
    create_magic_link_for_logout,
    verify_magic_link,
    create_user_from_token,
    create_access_token,
    create_refresh_token,
    verify_jwt_token
)
from app.models.user import User
from app.config import settings
from app.exceptions import InvalidTokenError

router = APIRouter(prefix="/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=MagicLinkResponse)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_period}seconds")
async def signup(
    request: Request,
    signup_data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user account and send magic link email.

    - Validates username and email uniqueness
    - Generates secure magic link token
    - Sends email with magic link
    - Rate limited to prevent abuse
    """
    await create_magic_link_for_signup(
        db,
        username=signup_data.username,
        email=signup_data.email
    )

    return MagicLinkResponse(
        message="Please check your email for the magic link to complete signup",
        email=signup_data.email
    )


@router.post("/login", response_model=MagicLinkResponse)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_period}seconds")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send magic link for user login.

    - Verifies user exists
    - Generates secure magic link token
    - Sends email with magic link
    - Rate limited to prevent abuse
    """
    await create_magic_link_for_login(db, email=login_data.email)

    return MagicLinkResponse(
        message="Please check your email for the magic link to sign in",
        email=login_data.email
    )


@router.get("/verify")
async def verify(
    token: str,
    response: Response,
    username: Optional[str] = None,
    action: str = "login",
    db: AsyncSession = Depends(get_db)
):
    """
    Verify magic link token.

    Handles signup, login, and logout flows:
    - For signup: Creates new user account (requires username parameter)
    - For login: Authenticates existing user
    - For logout: Clears authentication cookies
    - Sets httpOnly cookies with JWT tokens for login/signup
    - Redirects to appropriate page after verification
    """
    # Determine if this is signup, login, or logout
    from app.services.token_service import verify_token as check_token
    magic_link = await check_token(db, token)

    if action == "logout":
        # Logout flow - verify token and clear cookies
        user = await verify_magic_link(db, token)
        # Redirect to login page with success message
        redirect_url = f"{settings.frontend_url}/login.html?logout=success"
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return response

    if magic_link.user_id is None:
        # Signup flow - use username stored in token, fall back to URL param
        effective_username = magic_link.username or username
        if not effective_username:
            raise InvalidTokenError("Username required for signup")

        user = await create_user_from_token(db, token, effective_username)
    else:
        # Login flow
        user = await verify_magic_link(db, token)

    # Generate JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Set httpOnly cookies (secure=False for local development)
    use_secure = settings.frontend_url.startswith("https://")

    # Redirect to betting page after successful login/signup
    redirect_url = f"{settings.frontend_url}/betting.html"
    response = RedirectResponse(url=redirect_url, status_code=302)

    # Set cookies on the redirect response
    # Use SameSite=None with Secure=True for HTTPS, lax for HTTP (local dev)
    samesite = "none" if use_secure else "lax"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=use_secure,
        samesite=samesite,
        max_age=settings.access_token_expire_minutes * 60
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=use_secure,
        samesite=samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )

    return response


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    - Validates refresh token from cookie
    - Generates new access token
    - Sets new access token cookie
    - Returns user data
    """
    if not refresh_token:
        from app.exceptions import AuthenticationError
        raise AuthenticationError("Refresh token required")

    # Verify refresh token
    user = await verify_jwt_token(db, refresh_token, token_type="refresh")

    # Generate new access token
    new_access_token = create_access_token(user.id)

    # Set new access token cookie (secure=False for local development)
    use_secure = settings.frontend_url.startswith("https://")
    samesite = "none" if use_secure else "lax"

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=use_secure,
        samesite=samesite,
        max_age=settings.access_token_expire_minutes * 60
    )

    return RefreshResponse(
        message="Token refreshed successfully",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", response_model=MagicLinkResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Request logout by sending magic link via email.

    - Requires valid authentication
    - Generates secure magic link token
    - Sends email with logout confirmation link
    """
    await create_magic_link_for_logout(db, current_user)

    return MagicLinkResponse(
        message="Please check your email to confirm logout",
        email=current_user.email
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user data.

    - Requires valid access token in cookie
    - Returns user profile information
    """
    data = UserResponse.model_validate(current_user)
    data.is_admin = current_user.email in settings.admin_emails
    return data
