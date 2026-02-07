"""Tests for betting module."""

import uuid
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models.user import User
from app.models.league import League, LeagueMembership
from app.models.match import Match
from app.models.bet import Bet, UserBalance, BetStatus, BetOutcome
from app.services.bet_service import (
    place_bet,
    get_user_bets,
    get_user_balance,
    settle_bets,
    get_match_odds,
)
from app.exceptions import InsufficientFundsError, InvalidInputError


@pytest.mark.asyncio
class TestBettingService:
    """Test betting service logic."""

    async def test_place_bet_success(self, db, client):
        """Test placing a bet successfully."""
        # Create test data
        user = User(id=uuid.uuid4(), username="bettor", email="bettor@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST01", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.flush()

        # Place bet
        bet = await place_bet(
            db,
            user.id,
            match.id,
            league.id,
            "home_win",
            100.0,
        )

        await db.commit()

        assert bet.user_id == user.id
        assert bet.match_id == match.id
        assert bet.outcome == "home_win"
        assert bet.stake == 100.0
        assert bet.odds == 2.0
        assert bet.potential_payout == 200.0
        assert bet.status == BetStatus.PENDING

    async def test_place_bet_insufficient_funds(self, db, client):
        """Test placing bet with insufficient balance."""
        user = User(id=uuid.uuid4(), username="poor_bettor", email="poor@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST02", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.flush()

        # Create balance with low funds
        balance = UserBalance(user_id=user.id, balance=50.0)
        db.add(balance)
        await db.flush()

        # Try to place bet for more than balance
        with pytest.raises(InsufficientFundsError):
            await place_bet(
                db,
                user.id,
                match.id,
                league.id,
                "home_win",
                100.0,
            )

    async def test_place_bet_on_non_scheduled_match(self, db, client):
        """Test placing bet on non-scheduled match."""
        user = User(id=uuid.uuid4(), username="better2", email="better2@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST03", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() - timedelta(hours=2),
            venue="Stadium",
            status="completed",
            home_score=2,
            away_score=1,
        )

        db.add_all([user, league, match])
        await db.flush()

        # Try to place bet on completed match
        with pytest.raises(InvalidInputError):
            await place_bet(
                db,
                user.id,
                match.id,
                league.id,
                "home_win",
                100.0,
            )

    async def test_place_bet_invalid_outcome(self, db, client):
        """Test placing bet with invalid outcome."""
        user = User(id=uuid.uuid4(), username="better3", email="better3@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST04", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.flush()

        # Try to place bet with invalid outcome
        with pytest.raises(InvalidInputError):
            await place_bet(
                db,
                user.id,
                match.id,
                league.id,
                "invalid_outcome",
                100.0,
            )

    async def test_settle_bets_home_win(self, db, client):
        """Test settling bets when home team wins."""
        # Create users and bets
        user1 = User(id=uuid.uuid4(), username="user1", email="user1@test.com", is_active=True)
        user2 = User(id=uuid.uuid4(), username="user2", email="user2@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST05", creator_id=user1.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() - timedelta(hours=1),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user1, user2, league, match])
        await db.flush()

        # Create balances
        bal1 = UserBalance(user_id=user1.id, balance=900.0)  # 1000 - 100 bet
        bal2 = UserBalance(user_id=user2.id, balance=850.0)  # 1000 - 150 bet
        db.add_all([bal1, bal2])
        await db.flush()

        # Create bets
        bet1 = Bet(
            user_id=user1.id,
            match_id=match.id,
            league_id=league.id,
            outcome="home_win",
            stake=100.0,
            odds=2.0,
            potential_payout=200.0,
            status=BetStatus.PENDING,
        )
        bet2 = Bet(
            user_id=user2.id,
            match_id=match.id,
            league_id=league.id,
            outcome="away_win",
            stake=150.0,
            odds=3.0,
            potential_payout=450.0,
            status=BetStatus.PENDING,
        )

        db.add_all([bet1, bet2])
        await db.flush()

        # Settle bets
        settled_count = await settle_bets(db, match.id, 2, 1)  # Home team wins 2-1

        await db.commit()

        # Verify results
        assert settled_count == 2

        # Check bet1 (home_win) - WON
        result1 = await db.execute(select(Bet).where(Bet.id == bet1.id))
        settled_bet1 = result1.scalar_one()
        assert settled_bet1.status == BetStatus.WON
        assert settled_bet1.actual_payout == 200.0

        # Check bet2 (away_win) - LOST
        result2 = await db.execute(select(Bet).where(Bet.id == bet2.id))
        settled_bet2 = result2.scalar_one()
        assert settled_bet2.status == BetStatus.LOST
        assert settled_bet2.actual_payout == 0

        # Check balances updated
        result_bal1 = await db.execute(select(UserBalance).where(UserBalance.user_id == user1.id))
        balance1 = result_bal1.scalar_one()
        assert balance1.balance == 1100.0  # 900 + 200 payout

        result_bal2 = await db.execute(select(UserBalance).where(UserBalance.user_id == user2.id))
        balance2 = result_bal2.scalar_one()
        assert balance2.balance == 850.0  # Lost bet, no change

    async def test_settle_bets_draw_push(self, db, client):
        """Test settling bet on draw results in push (refund)."""
        user = User(id=uuid.uuid4(), username="user3", email="user3@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST06", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() - timedelta(hours=1),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.flush()

        bal = UserBalance(user_id=user.id, balance=800.0)  # 1000 - 200 bet
        db.add(bal)
        await db.flush()

        bet = Bet(
            user_id=user.id,
            match_id=match.id,
            league_id=league.id,
            outcome="home_win",
            stake=200.0,
            odds=2.0,
            potential_payout=400.0,
            status=BetStatus.PENDING,
        )

        db.add(bet)
        await db.flush()

        # Settle with draw
        await settle_bets(db, match.id, 1, 1)
        await db.commit()

        # Check bet status
        result = await db.execute(select(Bet).where(Bet.id == bet.id))
        settled_bet = result.scalar_one()
        assert settled_bet.status == BetStatus.PUSH
        assert settled_bet.actual_payout == 200.0  # Refunded

        # Check balance (refunded)
        result_bal = await db.execute(select(UserBalance).where(UserBalance.user_id == user.id))
        balance = result_bal.scalar_one()
        assert balance.balance == 1000.0  # 800 + 200 refund

    async def test_get_user_bets(self, db, client):
        """Test retrieving user bets."""
        user = User(id=uuid.uuid4(), username="user4", email="user4@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TEST07", creator_id=user.id)
        match1 = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )
        match2 = Match(
            id=uuid.uuid4(),
            home_team="Team C",
            away_team="Team D",
            match_datetime=datetime.utcnow() + timedelta(hours=4),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match1, match2])
        await db.flush()

        bet1 = Bet(
            user_id=user.id,
            match_id=match1.id,
            league_id=league.id,
            outcome="home_win",
            stake=100.0,
            odds=2.0,
            potential_payout=200.0,
            status=BetStatus.PENDING,
        )
        bet2 = Bet(
            user_id=user.id,
            match_id=match2.id,
            league_id=league.id,
            outcome="draw",
            stake=50.0,
            odds=3.5,
            potential_payout=175.0,
            status=BetStatus.PENDING,
        )

        db.add_all([bet1, bet2])
        await db.commit()

        # Get all bets
        bets = await get_user_bets(db, user.id)
        assert len(bets) == 2

        # Get bets for league
        bets_league = await get_user_bets(db, user.id, league.id)
        assert len(bets_league) == 2

        # Get pending bets
        bets_pending = await get_user_bets(db, user.id, status=BetStatus.PENDING)
        assert len(bets_pending) == 2

    async def test_get_user_balance_creates_default(self, db, client):
        """Test getting balance creates default if doesn't exist."""
        user = User(id=uuid.uuid4(), username="user5", email="user5@test.com", is_active=True)
        db.add(user)
        await db.flush()

        balance = await get_user_balance(db, user.id)

        assert balance.user_id == user.id
        assert balance.balance == 1000.0  # Default
        assert balance.total_wagered == 0.0
        assert balance.total_winnings == 0.0

    async def test_get_match_odds(self, db, client):
        """Test getting match odds."""
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add(match)
        await db.flush()

        odds = await get_match_odds(db, match)

        assert odds.match_id == match.id
        assert odds.home_team == "Team A"
        assert odds.away_team == "Team B"
        assert len(odds.outcomes) == 3

        # Check specific odds
        home_win = next(o for o in odds.outcomes if o.outcome == "home_win")
        assert home_win.odds == 2.0
        assert home_win.implied_probability > 0


@pytest.mark.asyncio
class TestBettingEndpoints:
    """Test betting API endpoints."""

    async def test_get_match_odds_endpoint(self, client, db):
        """Test GET /bets/match/{match_id}/odds endpoint."""
        # Setup
        user = User(id=uuid.uuid4(), username="testuser_odds", email="testuser_odds@test.com", is_active=True)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, match])
        await db.commit()

        # Setup auth
        async def override_get_current_user():
            return user

        from app.dependencies import get_current_user
        from app.main import app
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Test endpoint
            response = await client.get(f"/bets/match/{match.id}/odds")
            assert response.status_code == 200

            data = response.json()
            assert data["match_id"] == str(match.id)
            assert data["home_team"] == "Team A"
            assert data["away_team"] == "Team B"
            assert len(data["outcomes"]) == 3
        finally:
            app.dependency_overrides.clear()

    async def test_place_bet_endpoint(self, client, db):
        """Test POST /bets endpoint."""
        # Setup
        user = User(id=uuid.uuid4(), username="testuser_bet", email="testuser_bet@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TESTBET01", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.commit()

        # Setup auth
        async def override_get_current_user():
            return user

        from app.dependencies import get_current_user
        from app.main import app
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Place bet
            response = await client.post(
                "/bets",
                json={
                    "match_id": str(match.id),
                    "league_id": str(league.id),
                    "outcome": "home_win",
                    "stake": 100.0,
                },
            )

            assert response.status_code == 201

            data = response.json()
            assert data["outcome"] == "home_win"
            assert data["stake"] == 100.0
            assert data["odds"] == 2.0
            assert data["potential_payout"] == 200.0
            assert data["status"] == "pending"
        finally:
            app.dependency_overrides.clear()

    async def test_get_balance_endpoint(self, client, db):
        """Test GET /bets/balance endpoint."""
        # Setup
        user = User(id=uuid.uuid4(), username="testuser_balance", email="testuser_balance@test.com", is_active=True)
        db.add(user)
        await db.commit()

        # Setup auth
        async def override_get_current_user():
            return user

        from app.dependencies import get_current_user
        from app.main import app
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.get("/bets/balance")
            assert response.status_code == 200

            data = response.json()
            assert data["user_id"] == str(user.id)
            assert data["balance"] == 1000.0
            assert data["total_wagered"] == 0.0
            assert data["total_winnings"] == 0.0
        finally:
            app.dependency_overrides.clear()

    async def test_get_bets_history_endpoint(self, client, db):
        """Test GET /bets endpoint for bet history."""
        # Setup
        user = User(id=uuid.uuid4(), username="testuser_history", email="testuser_history@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TESTHIST01", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.flush()

        bet = Bet(
            user_id=user.id,
            match_id=match.id,
            league_id=league.id,
            outcome="home_win",
            stake=100.0,
            odds=2.0,
            potential_payout=200.0,
            status=BetStatus.PENDING,
        )

        db.add(bet)
        await db.commit()

        # Setup auth
        async def override_get_current_user():
            return user

        from app.dependencies import get_current_user
        from app.main import app
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.get("/bets")
            assert response.status_code == 200

            data = response.json()
            assert len(data) == 1
            assert data[0]["outcome"] == "home_win"
            assert data[0]["status"] == "pending"
        finally:
            app.dependency_overrides.clear()

    async def test_place_bet_insufficient_funds_error(self, client, db):
        """Test placing bet with insufficient funds returns 400."""
        # Setup
        user = User(id=uuid.uuid4(), username="testuser_poor", email="testuser_poor@test.com", is_active=True)
        league = League(id=uuid.uuid4(), name="Test League", code="TESTPOOR01", creator_id=user.id)
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=datetime.utcnow() + timedelta(hours=2),
            venue="Stadium",
            status="scheduled",
        )

        db.add_all([user, league, match])
        await db.flush()

        # Set low balance
        balance = UserBalance(user_id=user.id, balance=50.0)
        db.add(balance)
        await db.commit()

        # Setup auth
        async def override_get_current_user():
            return user

        from app.dependencies import get_current_user
        from app.main import app
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.post(
                "/bets",
                json={
                    "match_id": str(match.id),
                    "league_id": str(league.id),
                    "outcome": "home_win",
                    "stake": 100.0,
                },
            )

            assert response.status_code == 400
            assert "Insufficient balance" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
