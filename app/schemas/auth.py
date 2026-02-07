import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class SignupRequest(BaseModel):
    """Request model for user signup."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters, underscores, and hyphens."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response model for magic link generation."""

    message: str
    email: str

    @field_validator("email")
    @classmethod
    def mask_email(cls, v: str) -> str:
        """Mask email for privacy (e.g., j***@example.com)."""
        if "@" not in v:
            return v
        local, domain = v.split("@", 1)
        if len(local) <= 1:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}***@{domain}"


class UserResponse(BaseModel):
    """Response model for user data."""

    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class VerifyResponse(BaseModel):
    """Response model for magic link verification."""

    message: str
    user: UserResponse


class RefreshResponse(BaseModel):
    """Response model for token refresh."""

    message: str
    user: UserResponse


class LogoutResponse(BaseModel):
    """Response model for logout."""

    message: str
