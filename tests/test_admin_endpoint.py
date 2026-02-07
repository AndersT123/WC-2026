"""Integration tests for admin endpoint."""
import uuid
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.user import User
from app.models.league import League, LeagueMembership
from app.schemas.match import UpdateMatchResultRequest


@pytest.mark.asyncio
async def test_update_match_result_admin_only(client, admin_user, db):
    """Test that only admin can update match results."""
    # Create test data
    league = League(
        id=uuid.uuid4(),
        name="Test League",
        code="TEST",
        creator_id=admin_user.id,
        is_active=True,
    )
    db.add(league)

    match = Match(
        id=uuid.uuid4(),
        home_team="Home",
        away_team="Away",
        match_datetime=datetime.utcnow() + timedelta(hours=1),
        status="scheduled",
    )
    db.add(match)
    await db.flush()

    membership = LeagueMembership(
        id=uuid.uuid4(),
        user_id=admin_user.id,
        league_id=league.id,
        role="member",
    )
    db.add(membership)

    prediction = Prediction(
        id=uuid.uuid4(),
        user_id=admin_user.id,
        match_id=match.id,
        league_id=league.id,
        home_score=1,
        away_score=0,
    )
    db.add(prediction)
    await db.commit()

    # Test as admin
    response = await client.put(
        f"/matches/{match.id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    assert data["status"] == "completed"

    # Verify prediction was scored
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction.id)
    )
    pred = result.scalar_one()
    assert pred.points_earned is not None


@pytest.mark.asyncio
async def test_update_match_result_non_admin_forbidden(client, regular_user, db):
    """Test that non-admin users cannot update match results."""
    match_id = uuid.uuid4()

    response = await client.put(
        f"/matches/{match_id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        },
        headers={"Authorization": f"Bearer {regular_user}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_match_result_invalid_scores(client, admin_user):
    """Test that invalid scores are rejected."""
    match_id = uuid.uuid4()

    response = await client.put(
        f"/matches/{match_id}/result",
        json={
            "home_score": -1,
            "away_score": 1,
            "status": "completed"
        }
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_match_result_invalid_status(client, admin_user):
    """Test that invalid status is rejected."""
    match_id = uuid.uuid4()

    response = await client.put(
        f"/matches/{match_id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "invalid_status"
        }
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_nonexistent_match(client, admin_user):
    """Test that updating nonexistent match returns 404."""
    match_id = uuid.uuid4()

    response = await client.put(
        f"/matches/{match_id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_cannot_update_match(client):
    """Test that unauthenticated users cannot update matches."""
    match_id = uuid.uuid4()

    # No authentication
    response = await client.put(
        f"/matches/{match_id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_prediction_points_calculated_correctly(client, admin_user, db):
    """Test that prediction points are calculated using Witt Classic scoring."""
    # Create test data
    league = League(
        id=uuid.uuid4(),
        name="Test League",
        code="TEST2",
        creator_id=admin_user.id,
        is_active=True,
    )
    db.add(league)

    match = Match(
        id=uuid.uuid4(),
        home_team="Home",
        away_team="Away",
        match_datetime=datetime.utcnow() + timedelta(hours=1),
        status="scheduled",
    )
    db.add(match)
    await db.flush()

    membership = LeagueMembership(
        id=uuid.uuid4(),
        user_id=admin_user.id,
        league_id=league.id,
        role="member",
    )
    db.add(membership)

    # Create prediction: predict 2-1
    prediction = Prediction(
        id=uuid.uuid4(),
        user_id=admin_user.id,
        match_id=match.id,
        league_id=league.id,
        home_score=2,
        away_score=1,
    )
    db.add(prediction)
    await db.commit()

    # Set actual result: 2-1 (exact match)
    response = await client.put(
        f"/matches/{match.id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
    )

    assert response.status_code == 200

    # Verify exact score gives 5 points
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction.id)
    )
    pred = result.scalar_one()
    assert pred.points_earned == 5


@pytest.mark.asyncio
async def test_match_status_update(client, admin_user, db):
    """Test that match status is updated correctly."""
    match = Match(
        id=uuid.uuid4(),
        home_team="Home",
        away_team="Away",
        match_datetime=datetime.utcnow() + timedelta(hours=1),
        status="scheduled",
    )
    db.add(match)
    await db.commit()

    # Update to in_progress
    response = await client.put(
        f"/matches/{match.id}/result",
        json={
            "home_score": 1,
            "away_score": 0,
            "status": "in_progress"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"

    # Update to completed
    response = await client.put(
        f"/matches/{match.id}/result",
        json={
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
