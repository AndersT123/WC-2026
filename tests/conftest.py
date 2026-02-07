"""
Pytest configuration and fixtures for testing.

Supports two modes via PYTEST_MODE environment variable:
1. Unit Testing (default): Fresh database for each test
   Run: pytest tests/

2. Session Testing: Persistent database
   Run: PYTEST_MODE=session pytest tests/
"""

import asyncio
import os
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.config import settings
from app.database import Base, get_db


# Detect test mode from environment variable
TEST_MODE = os.getenv("PYTEST_MODE", "unit").lower()
IS_SESSION_MODE = TEST_MODE == "session"

# Configure database URL based on mode
if IS_SESSION_MODE:
    SESSION_DB_PATH = Path(__file__).parent.parent / "session.db"
    DATABASE_URL = f"sqlite+aiosqlite:///{SESSION_DB_PATH}"
    print(f"\n📁 Session Mode: Persistent database at {SESSION_DB_PATH}\n")
else:
    DATABASE_URL = settings.database_url


@pytest.fixture
async def db():
    """Create a test database session."""
    # Create async engine for testing
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )

    # Setup database
    async with engine.begin() as conn:
        if IS_SESSION_MODE:
            # Session mode: Create tables if they don't exist (preserve data)
            await conn.run_sync(Base.metadata.create_all)
        else:
            # Unit mode: Fresh database for each test
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        if not IS_SESSION_MODE:
            await session.rollback()
        # Session mode: Don't rollback - keep data

    # Cleanup
    if not IS_SESSION_MODE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(db):
    """Create an async test client."""
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
