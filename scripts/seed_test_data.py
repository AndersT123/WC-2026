"""
Test data seeder - Creates test users, leagues, matches, and predictions
for end-to-end testing without needing magic link authentication.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
sys.path.insert(0, '/home/anders/hello-scaleway')

from app.config import settings
from app.database import Base
from app.models.user import User, MagicLinkToken
from app.models.league import League, LeagueMembership
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.bet import Bet

# Test user credentials
TEST_USERS = [
    {"username": "alice", "email": "alice@test.com"},
    {"username": "bob", "email": "bob@test.com"},
    {"username": "charlie", "email": "charlie@test.com"},
    {"username": "diana", "email": "diana@test.com"},
]

async def seed_test_data():
    """Create test data in database."""
    # Setup database
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        future=True,
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        print("\n" + "="*70)
        print("SEEDING TEST DATA")
        print("="*70)

        # 1. Create test users
        print("\n1. Creating test users...")
        users = {}
        for user_data in TEST_USERS:
            user = User(
                id=uuid.uuid4(),
                username=user_data["username"],
                email=user_data["email"],
                is_active=True,
            )
            session.add(user)
            users[user_data["username"]] = user
            print(f"   ✓ Created user: {user_data['username']} ({user_data['email']})")

        await session.flush()

        # 2. Create leagues
        print("\n2. Creating leagues...")
        league1 = League(
            id=uuid.uuid4(),
            name="Test League 1",
            code="TEST0001",
            creator_id=users["alice"].id,
            is_active=True,
        )
        league2 = League(
            id=uuid.uuid4(),
            name="Test League 2",
            code="TEST0002",
            creator_id=users["bob"].id,
            is_active=True,
        )
        session.add(league1)
        session.add(league2)
        await session.flush()
        print(f"   ✓ Created league: {league1.name} (Code: {league1.code})")
        print(f"   ✓ Created league: {league2.name} (Code: {league2.code})")

        # 3. Add users to leagues
        print("\n3. Adding users to leagues...")

        # League 1: Alice (creator), Bob, Charlie
        members_league1 = [
            ("alice", "creator"),
            ("bob", "member"),
            ("charlie", "member"),
        ]

        for username, role in members_league1:
            membership = LeagueMembership(
                id=uuid.uuid4(),
                user_id=users[username].id,
                league_id=league1.id,
                role=role,
            )
            session.add(membership)
            print(f"   ✓ Added {username} to {league1.name} as {role}")

        # League 2: Bob (creator), Alice, Diana
        members_league2 = [
            ("bob", "creator"),
            ("alice", "member"),
            ("diana", "member"),
        ]

        for username, role in members_league2:
            membership = LeagueMembership(
                id=uuid.uuid4(),
                user_id=users[username].id,
                league_id=league2.id,
                role=role,
            )
            session.add(membership)
            print(f"   ✓ Added {username} to {league2.name} as {role}")

        await session.flush()

        # 4. Create matches
        print("\n4. Creating matches...")
        now = datetime.utcnow()

        # Past match (finished)
        match_past = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=now - timedelta(hours=2),
            venue="Stadium 1",
            status="completed",
            home_score=2,
            away_score=1,
        )

        # Current/upcoming matches (scheduled)
        match_upcoming1 = Match(
            id=uuid.uuid4(),
            home_team="Team C",
            away_team="Team D",
            match_datetime=now + timedelta(hours=2),
            venue="Stadium 2",
            status="scheduled",
        )

        match_upcoming2 = Match(
            id=uuid.uuid4(),
            home_team="Team E",
            away_team="Team F",
            match_datetime=now + timedelta(hours=4),
            venue="Stadium 3",
            status="scheduled",
        )

        match_upcoming3 = Match(
            id=uuid.uuid4(),
            home_team="Team G",
            away_team="Team H",
            match_datetime=now + timedelta(hours=6),
            venue="Stadium 4",
            status="scheduled",
        )

        matches = [match_past, match_upcoming1, match_upcoming2, match_upcoming3]
        for match in matches:
            session.add(match)
            status_info = f"(Score: {match.home_score}-{match.away_score})" if match.home_score is not None else "(Scheduled)"
            print(f"   ✓ Created match: {match.home_team} vs {match.away_team} {status_info}")

        await session.flush()

        # 5. Create predictions for past match
        print("\n5. Creating predictions for completed match...")
        predictions_data = [
            {"user": "alice", "league": league1, "match": match_past, "home": 2, "away": 1},  # Correct
            {"user": "bob", "league": league1, "match": match_past, "home": 2, "away": 0},    # Winner + 1 score
            {"user": "charlie", "league": league1, "match": match_past, "home": 1, "away": 1}, # Wrong
        ]

        for pred_data in predictions_data:
            prediction = Prediction(
                id=uuid.uuid4(),
                user_id=users[pred_data["user"]].id,
                match_id=pred_data["match"].id,
                league_id=pred_data["league"].id,
                home_score=pred_data["home"],
                away_score=pred_data["away"],
            )
            session.add(prediction)
            print(f"   ✓ Created prediction: {pred_data['user']} predicted {pred_data['home']}-{pred_data['away']}")

        await session.flush()

        # 6. Calculate points for completed match predictions
        print("\n6. Calculating prediction points...")
        from app.services.prediction_service import update_predictions_after_match

        updated_count = await update_predictions_after_match(session, match_past.id)
        print(f"   ✓ Calculated points for {updated_count} predictions")

        # 7. Create bets for past match
        print("\n7. Creating bets for completed match...")
        bets_data = [
            {"user": "alice", "league": league1, "match": match_past, "outcome": "home_win", "odds": 1.8, "status": "won", "payout": 1.8},
            {"user": "bob", "league": league1, "match": match_past, "outcome": "draw", "odds": 3.2, "status": "lost", "payout": 0},
            {"user": "charlie", "league": league1, "match": match_past, "outcome": "away_win", "odds": 2.5, "status": "lost", "payout": 0},
            {"user": "diana", "league": league2, "match": match_past, "outcome": "home_win", "odds": 1.8, "status": "won", "payout": 1.8},
        ]

        for bet_data in bets_data:
            bet = Bet(
                id=uuid.uuid4(),
                user_id=users[bet_data["user"]].id,
                match_id=bet_data["match"].id,
                outcome=bet_data["outcome"],
                odds=bet_data["odds"],
                status=bet_data["status"],
                actual_payout=bet_data["payout"],
                created_at=now - timedelta(hours=3),
                settled_at=now - timedelta(hours=1),
            )
            session.add(bet)
            print(f"   ✓ Created bet: {bet_data['user']} bet on {bet_data['outcome']} @ {bet_data['odds']} ({bet_data['status']})")

        await session.flush()

        # 8. Create predictions for upcoming matches
        print("\n8. Creating predictions for upcoming matches...")
        upcoming_predictions = [
            {"user": "alice", "league": league1, "match": match_upcoming1, "home": 1, "away": 0},
            {"user": "alice", "league": league1, "match": match_upcoming2, "home": 2, "away": 1},
            {"user": "bob", "league": league1, "match": match_upcoming1, "home": 0, "away": 0},
            {"user": "bob", "league": league1, "match": match_upcoming2, "home": 2, "away": 0},
            {"user": "charlie", "league": league1, "match": match_upcoming1, "home": 2, "away": 2},
            {"user": "alice", "league": league2, "match": match_upcoming3, "home": 1, "away": 1},
            {"user": "bob", "league": league2, "match": match_upcoming3, "home": 3, "away": 0},
            {"user": "diana", "league": league2, "match": match_upcoming3, "home": 2, "away": 1},
        ]

        for pred_data in upcoming_predictions:
            prediction = Prediction(
                id=uuid.uuid4(),
                user_id=users[pred_data["user"]].id,
                match_id=pred_data["match"].id,
                league_id=pred_data["league"].id,
                home_score=pred_data["home"],
                away_score=pred_data["away"],
            )
            session.add(prediction)
            print(f"   ✓ Created prediction: {pred_data['user']} predicted {pred_data['home']}-{pred_data['away']}")

        await session.flush()

        # 9. Create magic link tokens for test users (for login simulation)
        print("\n9. Creating login tokens...")
        # Use fixed tokens for local testing so they don't change
        fixed_tokens = {
            "alice": "test_token_alice_fixed123",
            "bob": "test_token_bob_fixed456",
            "charlie": "test_token_charlie_fixed789",
            "diana": "test_token_diana_fixed000",
        }
        for username, user in users.items():
            token = MagicLinkToken(
                id=uuid.uuid4(),
                token=fixed_tokens[username],
                user_id=user.id,
                email=user.email,
                expires_at=now + timedelta(hours=24),  # Extended to 24 hours
            )
            session.add(token)
            print(f"   ✓ Created token for: {username}")

        await session.flush()

        # Commit all changes
        await session.commit()

        # 10. Display summary
        print("\n" + "="*70)
        print("TEST DATA CREATED SUCCESSFULLY")
        print("="*70)

        print("\n📝 TEST USERS (Use these to test the application):")
        print("   Username        | Email           | Password")
        print("   " + "-" * 60)
        for user_data in TEST_USERS:
            print(f"   {user_data['username']:15} | {user_data['email']:15} | (use token below)")

        print("\n🔑 LOGIN TOKENS (Use these to authenticate in API):")
        for username, user in users.items():
            print(f"   {username}: test_token_{username}_*")
        print("\n   Note: Get exact tokens from database:")
        print("   SELECT email, token FROM magic_link_tokens WHERE email LIKE '%test.com%'")

        print("\n🏀 LEAGUES CREATED:")
        print(f"   • {league1.name} (Code: {league1.code})")
        print(f"     Members: alice (creator), bob, charlie")
        print(f"   • {league2.name} (Code: {league2.code})")
        print(f"     Members: bob (creator), alice, diana")

        print("\n⚽ MATCHES CREATED:")
        print(f"   • Completed: {match_past.home_team} vs {match_past.away_team} - Result: {match_past.home_score}-{match_past.away_score}")
        print(f"   • Scheduled: {match_upcoming1.home_team} vs {match_upcoming1.away_team}")
        print(f"   • Scheduled: {match_upcoming2.home_team} vs {match_upcoming2.away_team}")
        print(f"   • Scheduled: {match_upcoming3.home_team} vs {match_upcoming3.away_team}")

        print("\n📊 PREDICTIONS CREATED:")
        print(f"   • 3 predictions for completed match (with calculated points)")
        print(f"   • 8 predictions for upcoming matches (no points yet)")

        print("\n🎲 BETS CREATED:")
        print(f"   • 4 bets on completed match (Team A vs Team B):")
        print(f"     - alice: Home Win (1.8x) - WON")
        print(f"     - bob: Draw (3.2x) - LOST")
        print(f"     - charlie: Away Win (2.5x) - LOST")
        print(f"     - diana: Home Win (1.8x) - WON")

        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("\n1. Start the backend: python3 -m uvicorn app.main:app --port 8080")
        print("\n2. Use the database directly to get JWT tokens:")
        print("   sqlite3 worldcup.db \"SELECT email, token FROM magic_link_tokens WHERE email LIKE '%test.com%'\"")
        print("\n3. Or manually authenticate:")
        print("   - Go to http://localhost:8080/login.html")
        print("   - Use email: alice@test.com, bob@test.com, etc.")
        print("   - Check email for magic link (in test, this will be printed to console)")
        print("\n4. Run E2E tests:")
        print("   pytest tests/test_e2e.py -v")
        print("\n" + "="*70 + "\n")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_test_data())
