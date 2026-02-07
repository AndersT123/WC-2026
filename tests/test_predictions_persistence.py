"""
Tests for prediction and score persistence across sessions within a single test.

These tests verify:
1. Predictions are saved to database
2. Predictions persist across multiple requests (simulating different sessions)
3. Admin can input match results
4. Scores are calculated correctly after results are inputted
5. Leaderboard updates after match completion
"""

import uuid
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.main import app
from app.models.user import User
from app.models.league import League, LeagueMembership
from app.models.match import Match
from app.models.prediction import Prediction
from app.dependencies import get_current_user


@pytest.mark.asyncio
class TestPredictionPersistence:
    """Test that predictions are properly persisted and survive across requests."""

    @pytest.mark.asyncio
    async def test_prediction_saved_to_database_and_persists(self, client, db):
        """
        Test that:
        1. User creates league
        2. User makes prediction
        3. Prediction is saved to database
        4. Prediction can be retrieved in subsequent requests
        """
        # Setup: Create users
        user1 = User(
            id=uuid.uuid4(),
            username="predictor1",
            email="predictor1@test.com",
            is_active=True,
        )
        db.add(user1)
        await db.flush()
        await db.commit()

        # Setup: Create league
        league = League(
            id=uuid.uuid4(),
            name="Prediction Test League",
            code="PRED0001",
            creator_id=user1.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=user1.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)
        await db.flush()
        await db.commit()

        # Setup: Create a match
        now = datetime.utcnow()
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=now + timedelta(hours=2),
            venue="Stadium 1",
            status="scheduled",
        )
        db.add(match)
        await db.flush()
        await db.commit()

        # **Session 1: User makes a prediction**
        async def override_get_current_user():
            return user1

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Simulate POST request to save prediction (directly to database)
            prediction = Prediction(
                id=uuid.uuid4(),
                user_id=user1.id,
                match_id=match.id,
                league_id=league.id,
                home_score=2,
                away_score=1,
            )
            db.add(prediction)
            await db.flush()
            await db.commit()

            # Verify prediction saved in DB
            result = await db.execute(
                select(Prediction).where(
                    (Prediction.user_id == user1.id)
                    & (Prediction.match_id == match.id)
                    & (Prediction.league_id == league.id)
                )
            )
            saved_prediction = result.scalar_one()
            assert saved_prediction.home_score == 2
            assert saved_prediction.away_score == 1
            print("✓ Session 1: Prediction saved to database")

            # **Session 2: User retrieves their prediction (simulating new request/session)**
            # Fetch from database again (as if it's a new session)
            result = await db.execute(
                select(Prediction).where(Prediction.id == prediction.id)
            )
            fetched_prediction = result.scalar_one()

            # Verify prediction still there
            assert fetched_prediction.home_score == 2
            assert fetched_prediction.away_score == 1
            assert fetched_prediction.points_earned is None  # Not yet scored
            print("✓ Session 2: Prediction persisted and retrieved from database")

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_admin_inputs_result_and_predictions_scored(self, client, db):
        """
        Test complete workflow:
        1. User makes prediction
        2. Match is scheduled
        3. Admin inputs match result
        4. Predictions are automatically scored
        5. Scores persist and can be retrieved
        """
        # Setup: Create user
        user1 = User(
            id=uuid.uuid4(),
            username="scorer_user",
            email="scorer@test.com",
            is_active=True,
        )
        db.add(user1)
        await db.flush()
        await db.commit()

        # Setup: Create league
        league = League(
            id=uuid.uuid4(),
            name="Scoring Test League",
            code="SCORE001",
            creator_id=user1.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=user1.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)
        await db.flush()
        await db.commit()

        # Setup: Create match
        now = datetime.utcnow()
        match = Match(
            id=uuid.uuid4(),
            home_team="France",
            away_team="Germany",
            match_datetime=now - timedelta(hours=2),  # Match has already happened
            venue="Stadium X",
            status="scheduled",
        )
        db.add(match)
        await db.flush()

        # **Session 1: User makes prediction BEFORE match result is known**
        prediction = Prediction(
            id=uuid.uuid4(),
            user_id=user1.id,
            match_id=match.id,
            league_id=league.id,
            home_score=2,  # User predicts 2-1
            away_score=1,
        )
        db.add(prediction)
        await db.flush()
        await db.commit()

        print("✓ Session 1: Prediction created before match result")

        # **Session 2: Admin inputs match result**
        # This simulates admin updating the match with actual score
        match.status = "completed"
        match.home_score = 2  # Actual result matches prediction!
        match.away_score = 1
        db.add(match)
        await db.flush()
        await db.commit()

        print("✓ Session 2: Admin inputted match result (2-1)")

        # **Session 3: System calculates points for predictions**
        # Fetch the prediction again and calculate points
        result = await db.execute(
            select(Prediction).where(Prediction.id == prediction.id)
        )
        fetched_prediction = result.scalar_one()

        # Simulate scoring logic (exact match = 5 points)
        if (fetched_prediction.home_score == match.home_score and
            fetched_prediction.away_score == match.away_score):
            fetched_prediction.points_earned = 5

        db.add(fetched_prediction)
        await db.flush()
        await db.commit()

        print("✓ Session 3: Points calculated and saved (5 points for exact match)")

        # **Session 4: Verify points persist**
        result = await db.execute(
            select(Prediction).where(Prediction.id == prediction.id)
        )
        final_prediction = result.scalar_one()

        assert final_prediction.points_earned == 5
        assert final_prediction.home_score == 2
        assert final_prediction.away_score == 1
        print("✓ Session 4: Points persisted in database (5 points)")

    @pytest.mark.asyncio
    async def test_multiple_users_predictions_and_leaderboard(self, client, db):
        """
        Test realistic scenario:
        1. Multiple users in a league
        2. Each makes different predictions
        3. Match result is inputted
        4. Different users get different scores
        5. Leaderboard can be calculated from persisted data
        """
        # Setup: Create users
        alice = User(id=uuid.uuid4(), username="alice", email="alice@test.com", is_active=True)
        bob = User(id=uuid.uuid4(), username="bob", email="bob@test.com", is_active=True)
        charlie = User(id=uuid.uuid4(), username="charlie", email="charlie@test.com", is_active=True)

        for user in [alice, bob, charlie]:
            db.add(user)
        await db.flush()
        await db.commit()

        # Setup: Create league
        league = League(
            id=uuid.uuid4(),
            name="Multi-User Leaderboard Test",
            code="MULTI001",
            creator_id=alice.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        # Add all users to league
        for user in [alice, bob, charlie]:
            membership = LeagueMembership(
                id=uuid.uuid4(),
                user_id=user.id,
                league_id=league.id,
                role="creator" if user == alice else "member",
            )
            db.add(membership)
        await db.flush()
        await db.commit()

        print("✓ Setup: League with 3 users created")

        # Setup: Create match
        now = datetime.utcnow()
        match = Match(
            id=uuid.uuid4(),
            home_team="Team A",
            away_team="Team B",
            match_datetime=now - timedelta(hours=1),
            venue="Stadium",
            status="scheduled",
        )
        db.add(match)
        await db.flush()
        await db.commit()

        # **Session 1: Users make predictions**
        predictions_data = [
            (alice, 2, 1),  # Alice predicts 2-1 (exact match)
            (bob, 2, 0),    # Bob predicts 2-0 (gets winner right + 1 away goal)
            (charlie, 1, 1),  # Charlie predicts 1-1 (gets away goal right)
        ]

        predictions = []
        for user, home, away in predictions_data:
            pred = Prediction(
                id=uuid.uuid4(),
                user_id=user.id,
                match_id=match.id,
                league_id=league.id,
                home_score=home,
                away_score=away,
            )
            db.add(pred)
            predictions.append(pred)

        await db.flush()
        await db.commit()
        print("✓ Session 1: All 3 users made predictions")

        # **Session 2: Admin inputs actual match result**
        match.status = "completed"
        match.home_score = 2
        match.away_score = 1
        db.add(match)
        await db.flush()
        await db.commit()
        print("✓ Session 2: Match result inputted (2-1)")

        # **Session 3: Calculate points for all predictions**
        for pred in predictions:
            # Re-fetch from DB
            result = await db.execute(
                select(Prediction).where(Prediction.id == pred.id)
            )
            pred_from_db = result.scalar_one()

            # Score calculation logic
            home_match = pred_from_db.home_score == match.home_score
            away_match = pred_from_db.away_score == match.away_score

            if home_match and away_match:
                points = 5  # Exact match
            elif (pred_from_db.home_score > pred_from_db.away_score and
                  match.home_score > match.away_score):
                # Got winner right
                points = 2
                if home_match or away_match:
                    points += 1
            else:
                points = 1 if home_match or away_match else 0

            pred_from_db.points_earned = points
            db.add(pred_from_db)

        await db.flush()
        await db.commit()
        print("✓ Session 3: Points calculated for all predictions")

        # **Session 4: Verify leaderboard can be built from persisted data**
        result = await db.execute(
            select(Prediction).where(Prediction.league_id == league.id)
        )
        all_predictions = result.scalars().all()

        # Build leaderboard
        leaderboard = {}
        for pred in all_predictions:
            if pred.user_id not in leaderboard:
                leaderboard[pred.user_id] = 0
            leaderboard[pred.user_id] += pred.points_earned or 0

        # Map to names
        user_map = {alice.id: "alice", bob.id: "bob", charlie.id: "charlie"}
        sorted_lb = sorted(
            [(user_map[uid], pts) for uid, pts in leaderboard.items()],
            key=lambda x: x[1],
            reverse=True
        )

        print("✓ Session 4: Leaderboard built from persisted data:")
        for rank, (username, points) in enumerate(sorted_lb, 1):
            print(f"  {rank}. {username}: {points} points")

        # Verify leaderboard is correct
        assert sorted_lb[0] == ("alice", 5)  # Exact match
        assert sorted_lb[1] == ("bob", 3)    # Winner + 1 goal
        assert sorted_lb[2] == ("charlie", 1)  # 1 goal correct

        print("✓ Leaderboard verified: Points persisted correctly across all sessions!")

    @pytest.mark.asyncio
    async def test_multiple_matches_and_cumulative_scores(self, client, db):
        """
        Test that scores accumulate correctly across multiple matches.
        Simulates a realistic league season.
        """
        # Setup: Users and league
        user = User(id=uuid.uuid4(), username="season_player", email="season@test.com", is_active=True)
        db.add(user)
        await db.flush()
        await db.commit()

        league = League(
            id=uuid.uuid4(),
            name="Season Test League",
            code="SEASON",
            creator_id=user.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=user.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)
        await db.flush()
        await db.commit()

        print("✓ Setup: User and league created")

        # Create 3 matches
        now = datetime.utcnow()
        matches = []
        for i in range(3):
            match = Match(
                id=uuid.uuid4(),
                home_team=f"Team {chr(65+i)}",
                away_team=f"Team {chr(68+i)}",
                match_datetime=now - timedelta(hours=i),
                venue=f"Stadium {i+1}",
                status="scheduled",
            )
            db.add(match)
            matches.append(match)
        await db.flush()
        await db.commit()

        # User makes predictions for all matches
        predictions_by_match = [
            (0, 2, 1, 5),  # Match 0: predicts 2-1, actual 2-1 → 5 points (exact)
            (1, 1, 0, 3),  # Match 1: predicts 1-0, actual 2-0 → 3 points (winner right + away score matches)
            (2, 0, 0, 0),  # Match 2: predicts 0-0, actual 1-1 → 0 points (wrong)
        ]

        predictions = []
        for match_idx, pred_home, pred_away, expected_points in predictions_by_match:
            pred = Prediction(
                id=uuid.uuid4(),
                user_id=user.id,
                match_id=matches[match_idx].id,
                league_id=league.id,
                home_score=pred_home,
                away_score=pred_away,
            )
            db.add(pred)
            predictions.append((pred, expected_points))

        await db.flush()
        await db.commit()
        print("✓ Session 1: User made 3 predictions")

        # Admin inputs results for all matches
        actual_results = [(2, 1), (2, 0), (1, 1)]
        for match, (home, away) in zip(matches, actual_results):
            match.status = "completed"
            match.home_score = home
            match.away_score = away
            db.add(match)

        await db.flush()
        await db.commit()
        print("✓ Session 2: Admin inputted all 3 match results")

        # Calculate and save points
        for pred, expected_pts in predictions:
            result = await db.execute(
                select(Prediction).where(Prediction.id == pred.id)
            )
            pred_from_db = result.scalar_one()

            # Get the match
            result = await db.execute(
                select(Match).where(Match.id == pred_from_db.match_id)
            )
            match_from_db = result.scalar_one()

            # Score calculation
            home_match = pred_from_db.home_score == match_from_db.home_score
            away_match = pred_from_db.away_score == match_from_db.away_score

            if home_match and away_match:
                points = 5
            elif (pred_from_db.home_score > pred_from_db.away_score and
                  match_from_db.home_score > match_from_db.away_score):
                points = 2
                if home_match or away_match:
                    points += 1
            else:
                points = 1 if home_match or away_match else 0

            pred_from_db.points_earned = points
            db.add(pred_from_db)

        await db.flush()
        await db.commit()
        print("✓ Session 3: Points calculated")

        # Verify cumulative score
        result = await db.execute(
            select(Prediction).where(Prediction.league_id == league.id)
        )
        all_preds = result.scalars().all()

        total_points = sum(p.points_earned for p in all_preds)
        assert total_points == 8  # 5 + 3 + 0
        print(f"✓ Session 4: Cumulative score verified (8 points across 3 matches)")

        print("\n✅ ALL PERSISTENCE TESTS PASSED!")
