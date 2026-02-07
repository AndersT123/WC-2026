"""
Development-only endpoints for faster local testing.
These endpoints only work when running in development mode.
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.match import Match
from app.models.bet import Bet
from app.services.auth_service import create_access_token, create_refresh_token

router = APIRouter(prefix="/dev", tags=["development"])

# Only enable in development
IS_DEV = settings.frontend_url.startswith("http://localhost")


@router.get("/login/{username}")
async def dev_quick_login(
    username: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Quick login for development - instantly authenticates as a test user.

    Only available in development mode (localhost).

    Usage: GET http://localhost:8000/dev/login/bob
    """
    if not IS_DEV:
        return {"error": "Dev endpoints only available in development"}

    # Get user by username
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        return {"error": f"User '{username}' not found"}

    # Create JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Set httpOnly cookies
    use_secure = settings.frontend_url.startswith("https://")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=use_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=use_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )

    # Redirect to standings page
    response.headers["Location"] = "/league-standings.html"
    response.status_code = 302

    return response


@router.get("/test-users")
async def get_test_users(db: AsyncSession = Depends(get_db)):
    """Get list of available test users for dev login."""
    if not IS_DEV:
        return {"error": "Dev endpoints only available in development"}

    result = await db.execute(select(User).limit(10))
    users = result.scalars().all()

    return {
        "test_users": [
            {
                "username": user.username,
                "email": user.email,
                "login_url": f"/dev/login/{user.username}"
            }
            for user in users
        ]
    }


@router.post("/create-sample-matches")
async def create_sample_matches(db: AsyncSession = Depends(get_db)):
    """
    Create sample historical matches for testing betting and predictions UI.
    Only available in development mode.
    """
    if not IS_DEV:
        return {"error": "Dev endpoints only available in development"}

    # Sample matches with past dates
    sample_matches = [
        {
            "home_team": "Team A",
            "away_team": "Team B",
            "match_datetime": datetime.utcnow() - timedelta(days=10),
            "venue": "Stadium A",
            "status": "completed",
            "home_score": 2,
            "away_score": 1,
        },
        {
            "home_team": "Team C",
            "away_team": "Team D",
            "match_datetime": datetime.utcnow() - timedelta(days=8),
            "venue": "Stadium B",
            "status": "completed",
            "home_score": 1,
            "away_score": 1,
        },
        {
            "home_team": "Team E",
            "away_team": "Team F",
            "match_datetime": datetime.utcnow() - timedelta(days=5),
            "venue": "Stadium C",
            "status": "completed",
            "home_score": 3,
            "away_score": 0,
        },
        {
            "home_team": "Team G",
            "away_team": "Team H",
            "match_datetime": datetime.utcnow() - timedelta(days=2),
            "venue": "Stadium D",
            "status": "completed",
            "home_score": 0,
            "away_score": 2,
        },
    ]

    created_matches = []
    for match_data in sample_matches:
        # Check if match already exists
        result = await db.execute(
            select(Match).where(
                (Match.home_team == match_data["home_team"])
                & (Match.away_team == match_data["away_team"])
                & (Match.match_datetime == match_data["match_datetime"])
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            match = Match(
                id=uuid.uuid4(),
                home_team=match_data["home_team"],
                away_team=match_data["away_team"],
                match_datetime=match_data["match_datetime"],
                venue=match_data["venue"],
                status=match_data["status"],
                home_score=match_data["home_score"],
                away_score=match_data["away_score"],
            )
            db.add(match)
            created_matches.append(
                {
                    "id": str(match.id),
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "score": f"{match.home_score}-{match.away_score}",
                }
            )

    await db.commit()

    return {
        "message": f"Created {len(created_matches)} sample matches",
        "matches": created_matches,
    }


@router.post("/create-sample-bets")
async def create_sample_bets(db: AsyncSession = Depends(get_db)):
    """
    Create sample bets for all test users on historical matches.
    Only available in development mode.
    """
    if not IS_DEV:
        return {"error": "Dev endpoints only available in development"}

    # Get all completed matches
    result = await db.execute(
        select(Match).where(Match.status == "completed")
    )
    completed_matches = result.scalars().all()

    if not completed_matches:
        return {"message": "No completed matches found. Create sample matches first."}

    # Get test users
    test_usernames = ["alice", "bob", "diana", "charlie"]
    result = await db.execute(
        select(User).where(User.username.in_(test_usernames))
    )
    test_users = result.scalars().all()

    if not test_users:
        return {"error": "No test users found (alice, bob, diana, charlie)"}

    # Import LeagueMembership
    from app.models.league import LeagueMembership

    # Sample bets with different outcomes for variety
    bets_configs = [
        [
            {"match_index": 0, "outcome": "home_win", "odds": 1.8, "status": "won", "payout": 1.8},
            {"match_index": 1, "outcome": "draw", "odds": 3.2, "status": "won", "payout": 3.2},
            {"match_index": 2, "outcome": "away_win", "odds": 2.5, "status": "lost", "payout": 0},
            {"match_index": 3, "outcome": "home_win", "odds": 2.0, "status": "won", "payout": 2.0},
        ],
        [
            {"match_index": 0, "outcome": "draw", "odds": 2.5, "status": "lost", "payout": 0},
            {"match_index": 1, "outcome": "away_win", "odds": 2.8, "status": "lost", "payout": 0},
            {"match_index": 2, "outcome": "home_win", "odds": 1.5, "status": "won", "payout": 1.5},
            {"match_index": 3, "outcome": "draw", "odds": 3.0, "status": "lost", "payout": 0},
        ],
        [
            {"match_index": 0, "outcome": "away_win", "odds": 3.5, "status": "lost", "payout": 0},
            {"match_index": 1, "outcome": "draw", "odds": 3.2, "status": "won", "payout": 3.2},
            {"match_index": 2, "outcome": "home_win", "odds": 1.5, "status": "won", "payout": 1.5},
            {"match_index": 3, "outcome": "away_win", "odds": 2.0, "status": "won", "payout": 2.0},
        ],
        [
            {"match_index": 0, "outcome": "home_win", "odds": 1.8, "status": "won", "payout": 1.8},
            {"match_index": 1, "outcome": "draw", "odds": 3.2, "status": "won", "payout": 3.2},
            {"match_index": 2, "outcome": "home_win", "odds": 1.5, "status": "won", "payout": 1.5},
            {"match_index": 3, "outcome": "away_win", "odds": 2.0, "status": "won", "payout": 2.0},
        ],
    ]

    total_bets_created = 0

    for user, bets_config in zip(test_users, bets_configs):
        # Get user's first league
        result = await db.execute(
            select(LeagueMembership).where(
                LeagueMembership.user_id == user.id
            ).limit(1)
        )
        league_member = result.scalar_one_or_none()

        if not league_member:
            continue

        league_id = league_member.league_id

        # Create bets for this user
        for bet_data in bets_config:
            if bet_data["match_index"] >= len(completed_matches):
                continue

            match = completed_matches[bet_data["match_index"]]

            # Check if bet already exists
            result = await db.execute(
                select(Bet).where(
                    (Bet.user_id == user.id)
                    & (Bet.match_id == match.id)
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                bet = Bet(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    match_id=match.id,
                    league_id=league_id,
                    outcome=bet_data["outcome"],
                    odds=bet_data["odds"],
                    status=bet_data["status"],
                    actual_payout=bet_data["payout"],
                    created_at=datetime.utcnow(),
                    settled_at=datetime.utcnow(),
                )
                db.add(bet)
                total_bets_created += 1

    await db.commit()

    return {
        "message": f"Created {total_bets_created} sample bets for all test users",
        "users": ["alice", "bob", "diana", "charlie"],
    }


@router.post("/cleanup-sample-bets")
async def cleanup_sample_bets(db: AsyncSession = Depends(get_db)):
    """
    Remove bets from all matches except Team A vs Team B, and change other matches to scheduled.
    Only available in development mode.
    """
    if not IS_DEV:
        return {"error": "Dev endpoints only available in development"}

    # Get Team A vs Team B match
    result = await db.execute(
        select(Match).where(
            (Match.home_team == "Team A") & (Match.away_team == "Team B")
        )
    )
    team_a_b = result.scalar_one_or_none()

    if not team_a_b:
        return {"error": "Team A vs Team B match not found"}

    # Get other matches
    result = await db.execute(
        select(Match).where(Match.id != team_a_b.id)
    )
    other_matches = result.scalars().all()

    # Change other matches to scheduled (so they're available for betting/predictions)
    for match in other_matches:
        match.status = "scheduled"
        db.add(match)

    await db.commit()

    return {
        "message": f"Cleaned up database: kept Team A vs Team B as completed with bets, changed other matches to scheduled",
        "action": "Other matches now available for new bets/predictions",
    }
