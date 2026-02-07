from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./test.db"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120  # 2 hours
    refresh_token_expire_days: int = 30

    # Magic Link Settings
    magic_link_expire_minutes: int = 15

    # Email Settings (Brevo SMTP)
    from_email: str = "noreply@example.com"

    # SMTP Settings (Brevo)
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Frontend/Application URLs
    frontend_url: str = "http://localhost:3000"

    # Rate Limiting
    rate_limit_requests: int = 3
    rate_limit_period: int = 900  # 15 minutes in seconds

    # CORS Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Admin Configuration
    admin_emails_str: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def admin_emails(self) -> List[str]:
        """Parse comma-separated admin emails string into list."""
        if not self.admin_emails_str:
            return []
        return [email.strip() for email in self.admin_emails_str.split(",")]


# Global settings instance
settings = Settings()
