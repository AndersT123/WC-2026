#!/usr/bin/env python3
"""
Manage the persistent session testing database.

This script helps you:
- View database status
- Reset the database (drop all data)
- List tables and data counts
- Clear specific tables

Usage:
    python3 manage_session_db.py status      # Show database info
    python3 manage_session_db.py reset       # Reset entire database
    python3 manage_session_db.py tables      # List tables and row counts
    python3 manage_session_db.py clear users # Clear specific table
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import inspect, text, select, func

from app.database import Base
from app.models.user import User
from app.models.league import League, LeagueMembership
from app.models.match import Match
from app.models.prediction import Prediction

SESSION_DB_PATH = Path(__file__).parent / "session.db"
SESSION_DATABASE_URL = f"sqlite+aiosqlite:///{SESSION_DB_PATH}"


async def get_engine():
    """Create database engine."""
    return create_async_engine(
        SESSION_DATABASE_URL,
        echo=False,
        future=True,
    )


async def show_status():
    """Show database status."""
    print(f"\n📊 Session Database Status")
    print(f"{'='*60}")
    print(f"Database File: {SESSION_DB_PATH}")
    print(f"Path Exists: {SESSION_DB_PATH.exists()}")

    if SESSION_DB_PATH.exists():
        size_mb = SESSION_DB_PATH.stat().st_size / (1024 * 1024)
        print(f"Size: {size_mb:.2f} MB")

    engine = await get_engine()
    try:
        async with engine.begin() as conn:
            inspector = inspect(conn.sync_engine)
            tables = inspector.get_table_names()
            print(f"Tables: {len(tables)}")
            if tables:
                print(f"  - {', '.join(tables)}")
    finally:
        await engine.dispose()

    print(f"{'='*60}\n")


async def list_tables():
    """List all tables with row counts."""
    print(f"\n📋 Database Tables and Row Counts")
    print(f"{'='*60}")

    engine = await get_engine()

    try:
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            # Models to check
            models = [User, League, LeagueMembership, Match, Prediction]

            for model in models:
                try:
                    result = await session.execute(
                        select(func.count(model.id))
                    )
                    count = result.scalar() or 0
                    print(f"  {model.__name__:20} {count:>5} rows")
                except Exception as e:
                    print(f"  {model.__name__:20} ERROR: {e}")

    finally:
        await engine.dispose()

    print(f"{'='*60}\n")


async def reset_database():
    """Reset the database (drop and recreate all tables)."""
    print(f"\n⚠️  Resetting Session Database")
    print(f"{'='*60}")

    if SESSION_DB_PATH.exists():
        print(f"Current database: {SESSION_DB_PATH}")
        response = input("Delete all data? (yes/no): ").lower().strip()

        if response != "yes":
            print("❌ Cancelled")
            return

        SESSION_DB_PATH.unlink()
        print(f"✓ Deleted {SESSION_DB_PATH}")

    engine = await get_engine()

    try:
        # Create fresh tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        print(f"✓ Created fresh database at {SESSION_DB_PATH}")

    finally:
        await engine.dispose()

    print(f"{'='*60}\n")


async def clear_table(table_name):
    """Clear all data from a specific table."""
    print(f"\n🗑️  Clearing Table: {table_name}")
    print(f"{'='*60}")

    engine = await get_engine()

    try:
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            # Map table names to models
            models = {
                "users": User,
                "leagues": League,
                "league_memberships": LeagueMembership,
                "matches": Match,
                "predictions": Prediction,
            }

            if table_name not in models:
                print(f"❌ Unknown table: {table_name}")
                print(f"Available tables: {', '.join(models.keys())}")
                return

            model = models[table_name]

            # Get count before
            result = await session.execute(select(func.count(model.id)))
            before_count = result.scalar() or 0

            # Delete all
            await session.execute(text(f"DELETE FROM {table_name}"))
            await session.commit()

            print(f"✓ Cleared {before_count} rows from {table_name}")

    finally:
        await engine.dispose()

    print(f"{'='*60}\n")


async def main():
    """Main CLI handler."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "status":
        await show_status()
    elif command == "tables":
        await list_tables()
    elif command == "reset":
        await reset_database()
    elif command == "clear":
        if len(sys.argv) < 3:
            print("❌ Usage: python3 manage_session_db.py clear <table_name>")
            return
        table_name = sys.argv[2].lower()
        await clear_table(table_name)
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
