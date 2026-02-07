"""
Comprehensive HTTP endpoint tests for the league API.

Test Coverage:
1. League Creation - authenticated user creates league
2. League Joining - user joins with valid code
3. List User Leagues - retrieve all leagues user is member of
4. Get League Details - fetch single league with member count
5. Error Handling - invalid codes, duplicate joins, auth errors
6. Multi-user Scenarios - multiple users in same league
"""

import uuid
import pytest
from sqlalchemy import select

from app.main import app
from app.models.user import User
from app.models.league import League, LeagueMembership
from app.dependencies import get_current_user




@pytest.mark.asyncio
class TestLeagueCreation:
    """Tests for creating leagues."""

    @pytest.fixture
    async def authenticated_user(self, db):
        """Create and return an authenticated test user."""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.commit()
        await db.refresh(user)
        return user

    @pytest.fixture
    async def auth_client(self, client, db, authenticated_user):
        """Client with authentication override."""
        app.dependency_overrides.clear()  # Ensure clean state

        async def override_get_current_user():
            return authenticated_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_league_success(self, client, db):
        """User can create league and becomes creator."""
        user = User(
            id=uuid.uuid4(),
            username="testuser_create",
            email="test_create@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.commit()

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.post(
                "/leagues",
                json={"name": "My Test League", "description": "Test description"},
            )

            assert response.status_code == 201
            data = response.json()

            # Verify response structure
            assert data["name"] == "My Test League"
            assert data["description"] == "Test description"
            assert data["creator_id"] == str(user.id)
            assert "code" in data
            assert len(data["code"]) == 8
            assert data["is_active"] is True

            # Verify league in database
            result = await db.execute(
                select(League).where(League.code == data["code"])
            )
            league = result.scalar_one()
            assert league.name == "My Test League"
            assert league.creator_id == user.id

            # Verify creator membership
            result = await db.execute(
                select(LeagueMembership).where(
                    (LeagueMembership.league_id == league.id)
                    & (LeagueMembership.user_id == user.id)
                )
            )
            membership = result.scalar_one()
            assert membership.role == "creator"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_league_without_description(
        self, client, db
    ):
        """League can be created without description."""
        user = User(
            id=uuid.uuid4(),
            username="testuser_nodesc",
            email="test_nodesc@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.commit()

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.post(
                "/leagues",
                json={"name": "No Description League"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "No Description League"
            assert data["description"] is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_league_unique_code(self, client, db):
        """Each created league gets a unique 8-character code."""
        user = User(
            id=uuid.uuid4(),
            username="testuser_unique",
            email="test_unique@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.commit()

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            codes = set()

            for i in range(3):
                response = await client.post(
                    "/leagues",
                    json={"name": f"League {i}"},
                )
                assert response.status_code == 201
                code = response.json()["code"]
                assert len(code) == 8
                codes.add(code)

            assert len(codes) == 3  # All unique
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_league_unauthenticated(self, client):
        """Unauthenticated user cannot create league."""
        response = await client.post(
            "/leagues",
            json={"name": "Unauthorized League"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_league_invalid_name(self, auth_client):
        """Cannot create league with empty name."""
        response = await auth_client.post(
            "/leagues",
            json={"name": ""},
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestLeagueJoining:
    """Tests for joining leagues."""

    @pytest.fixture
    async def setup_league_and_users(self, db):
        """Create a league and multiple test users."""
        # Create users
        creator = User(
            id=uuid.uuid4(),
            username="creator",
            email="creator@test.com",
            is_active=True,
        )
        joiner = User(
            id=uuid.uuid4(),
            username="joiner",
            email="joiner@test.com",
            is_active=True,
        )
        non_member = User(
            id=uuid.uuid4(),
            username="nonmember",
            email="nonmember@test.com",
            is_active=True,
        )
        db.add_all([creator, joiner, non_member])
        await db.flush()

        # Create league
        league = League(
            id=uuid.uuid4(),
            name="Test League",
            code="TESTCODE",
            creator_id=creator.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        # Add creator as member
        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=creator.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)
        await db.flush()
        await db.commit()

        return {"league": league, "creator": creator, "joiner": joiner, "non_member": non_member}

    @pytest.fixture
    async def joiner_client(self, client, db, setup_league_and_users):
        """Client authenticated as the joiner user."""
        joiner = setup_league_and_users["joiner"]

        async def override_get_current_user():
            return joiner

        app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

    @pytest.fixture
    async def non_member_client(self, client, db, setup_league_and_users):
        """Client authenticated as a non-member user."""
        non_member = setup_league_and_users["non_member"]

        async def override_get_current_user():
            return non_member

        app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_join_league_with_valid_code(
        self, joiner_client, db, setup_league_and_users
    ):
        """User can join league with valid code."""
        league = setup_league_and_users["league"]
        joiner = setup_league_and_users["joiner"]

        response = await joiner_client.post(
            "/leagues/join",
            json={"code": league.code},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(league.id)
        assert data["name"] == league.name
        assert data["code"] == league.code

        # Verify membership in database
        result = await db.execute(
            select(LeagueMembership).where(
                (LeagueMembership.league_id == league.id)
                & (LeagueMembership.user_id == joiner.id)
            )
        )
        membership = result.scalar_one()
        assert membership.role == "member"

    @pytest.mark.asyncio
    async def test_join_league_invalid_code(self, joiner_client):
        """Cannot join league with invalid code."""
        response = await joiner_client.post(
            "/leagues/join",
            json={"code": "INVALID1"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_join_league_duplicate_membership(
        self, non_member_client, db, setup_league_and_users
    ):
        """User cannot join same league twice."""
        league = setup_league_and_users["league"]
        non_member = setup_league_and_users["non_member"]

        # First join succeeds
        response = await non_member_client.post(
            "/leagues/join",
            json={"code": league.code},
        )
        assert response.status_code == 200

        # Second join fails
        response = await non_member_client.post(
            "/leagues/join",
            json={"code": league.code},
        )
        assert response.status_code == 409
        data = response.json()
        assert "already a member" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_join_league_unauthenticated(self, client, setup_league_and_users):
        """Unauthenticated user cannot join league."""
        league = setup_league_and_users["league"]

        response = await client.post(
            "/leagues/join",
            json={"code": league.code},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_join_league_invalid_code_format(self, joiner_client):
        """Code must be exactly 8 characters."""
        # Too short
        response = await joiner_client.post(
            "/leagues/join",
            json={"code": "SHORT"},
        )
        assert response.status_code == 422

        # Too long
        response = await joiner_client.post(
            "/leagues/join",
            json={"code": "TOOLONGCODE"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListUserLeagues:
    """Tests for listing user's leagues."""

    @pytest.fixture
    async def setup_leagues_and_memberships(self, db):
        """Create user with multiple league memberships."""
        user = User(
            id=uuid.uuid4(),
            username="listuser",
            email="list@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        other_user = User(
            id=uuid.uuid4(),
            username="otheruser",
            email="other@test.com",
            is_active=True,
        )
        db.add(other_user)
        await db.flush()

        # Create 3 leagues user is in
        user_leagues = []
        for i in range(3):
            league = League(
                id=uuid.uuid4(),
                name=f"User League {i}",
                code=f"USR{i:05d}",
                creator_id=user.id if i == 0 else other_user.id,
                is_active=True,
            )
            db.add(league)
            user_leagues.append(league)
        await db.flush()

        # Create 1 league user is NOT in
        other_league = League(
            id=uuid.uuid4(),
            name="Other League",
            code="OTHER",
            creator_id=other_user.id,
            is_active=True,
        )
        db.add(other_league)
        await db.flush()

        # Add user to leagues
        for i, league in enumerate(user_leagues):
            role = "creator" if i == 0 else "member"
            membership = LeagueMembership(
                id=uuid.uuid4(),
                user_id=user.id,
                league_id=league.id,
                role=role,
            )
            db.add(membership)

        # Add other user to their leagues
        for i, league in enumerate(user_leagues):
            if i > 0:  # Only other leagues
                membership = LeagueMembership(
                    id=uuid.uuid4(),
                    user_id=other_user.id,
                    league_id=league.id,
                    role="member",
                )
                db.add(membership)

        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=other_user.id,
            league_id=other_league.id,
            role="creator",
        )
        db.add(membership)
        await db.flush()
        await db.commit()

        return {"user": user, "user_leagues": user_leagues, "other_league": other_league}

    @pytest.fixture
    async def list_client(self, client, db, setup_leagues_and_memberships):
        """Client authenticated as the list user."""
        user = setup_leagues_and_memberships["user"]

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_user_leagues(self, list_client, setup_leagues_and_memberships):
        """User can list all their leagues."""
        response = await list_client.get("/leagues")

        assert response.status_code == 200
        data = response.json()

        # Should have exactly 3 leagues
        assert len(data) == 3

        # Verify league names are present
        names = {league["name"] for league in data}
        expected_names = {"User League 0", "User League 1", "User League 2"}
        assert names == expected_names

        # Verify member counts are included
        for league in data:
            assert "member_count" in league
            assert league["member_count"] > 0

    @pytest.mark.asyncio
    async def test_list_user_leagues_empty(self, client, db):
        """Empty list for user with no leagues."""
        user = User(
            id=uuid.uuid4(),
            username="emptyuser",
            email="empty@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await client.get("/leagues")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_leagues_unauthenticated(self, client):
        """Unauthenticated user cannot list leagues."""
        response = await client.get("/leagues")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_leagues_member_count_accuracy(
        self, list_client, db, setup_leagues_and_memberships
    ):
        """Member counts are accurate in league list."""
        user = setup_leagues_and_memberships["user"]
        user_leagues = setup_leagues_and_memberships["user_leagues"]

        response = await list_client.get("/leagues")
        assert response.status_code == 200
        data = response.json()

        # First league should have 1 member (creator only)
        league_0 = next(l for l in data if l["name"] == "User League 0")
        assert league_0["member_count"] == 1

        # Other leagues should have 2 members (user + other_user)
        league_1 = next(l for l in data if l["name"] == "User League 1")
        assert league_1["member_count"] == 2


@pytest.mark.asyncio
class TestGetLeagueDetails:
    """Tests for getting league details."""

    @pytest.fixture
    async def setup_league_with_members(self, db):
        """Create league with multiple members."""
        creator = User(
            id=uuid.uuid4(),
            username="detailcreator",
            email="detailcreator@test.com",
            is_active=True,
        )
        db.add(creator)
        await db.flush()

        league = League(
            id=uuid.uuid4(),
            name="Detail Test League",
            code="DETL001",
            creator_id=creator.id,
            is_active=True,
            description="A league for testing details",
        )
        db.add(league)
        await db.flush()

        # Add creator
        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=creator.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)

        # Add members
        for i in range(3):
            member = User(
                id=uuid.uuid4(),
                username=f"member{i}",
                email=f"member{i}@test.com",
                is_active=True,
            )
            db.add(member)
            await db.flush()

            membership = LeagueMembership(
                id=uuid.uuid4(),
                user_id=member.id,
                league_id=league.id,
                role="member",
            )
            db.add(membership)

        await db.flush()
        await db.commit()
        return {"league": league, "creator": creator}

    @pytest.fixture
    async def detail_client(self, client, db, setup_league_with_members):
        """Client authenticated as creator."""
        creator = setup_league_with_members["creator"]

        async def override_get_current_user():
            return creator

        app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_league_details_success(
        self, detail_client, setup_league_with_members
    ):
        """User can get league details."""
        league = setup_league_with_members["league"]

        response = await detail_client.get(f"/leagues/{league.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(league.id)
        assert data["name"] == "Detail Test League"
        assert data["code"] == "DETL001"
        assert data["description"] == "A league for testing details"
        assert data["member_count"] == 4  # Creator + 3 members

    @pytest.mark.asyncio
    async def test_get_league_details_nonexistent(self, detail_client):
        """Getting non-existent league returns 404."""
        fake_id = uuid.uuid4()

        response = await detail_client.get(f"/leagues/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_league_details_unauthenticated(self, client, setup_league_with_members):
        """Unauthenticated user cannot get league details."""
        league = setup_league_with_members["league"]

        response = await client.get(f"/leagues/{league.id}")

        assert response.status_code == 401


@pytest.mark.asyncio
class TestMultiUserScenarios:
    """Tests for multi-user league scenarios."""

    @pytest.mark.asyncio
    async def test_league_creator_and_members_visible_in_member_count(self, client, db):
        """Both creator and members are counted in member_count."""
        creator = User(
            id=uuid.uuid4(),
            username="count_creator",
            email="count_creator@test.com",
            is_active=True,
        )
        db.add(creator)
        await db.flush()

        league = League(
            id=uuid.uuid4(),
            name="Count Test League",
            code="COUNT01",
            creator_id=creator.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        # Add creator
        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=creator.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)

        # Add 5 members
        for i in range(5):
            member = User(
                id=uuid.uuid4(),
                username=f"counter{i}",
                email=f"counter{i}@test.com",
                is_active=True,
            )
            db.add(member)
            await db.flush()

            membership = LeagueMembership(
                id=uuid.uuid4(),
                user_id=member.id,
                league_id=league.id,
                role="member",
            )
            db.add(membership)

        await db.flush()
        await db.commit()

        # Get league details
        async def override_get_current_user():
            return creator

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.get(f"/leagues/{league.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["member_count"] == 6  # Creator + 5 members
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_user_memberships_persist_across_requests(self, client, db):
        """User's league membership persists across multiple requests."""
        user = User(
            id=uuid.uuid4(),
            username="persist_user",
            email="persist@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        league = League(
            id=uuid.uuid4(),
            name="Persistence League",
            code="PERS001",
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

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # First request - list leagues
            response = await client.get("/leagues")
            assert response.status_code == 200
            assert len(response.json()) == 1

            # Second request - get details
            response = await client.get(f"/leagues/{league.id}")
            assert response.status_code == 200
            assert response.json()["name"] == "Persistence League"

            # Third request - list again
            response = await client.get("/leagues")
            assert response.status_code == 200
            assert len(response.json()) == 1
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestLeagueErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_cannot_join_with_empty_code(self, client, db):
        """Cannot join league with empty code."""
        user = User(
            id=uuid.uuid4(),
            username="emptycode_user",
            email="emptycode@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await client.post(
            "/leagues/join",
            json={"code": ""},
        )

        assert response.status_code == 422  # Validation error

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_league_code_is_case_sensitive(self, client, db):
        """League codes are case-sensitive for joining."""
        creator = User(
            id=uuid.uuid4(),
            username="case_creator",
            email="case_creator@test.com",
            is_active=True,
        )
        db.add(creator)
        await db.flush()

        league = League(
            id=uuid.uuid4(),
            name="Case Test",
            code="CASETEST",
            creator_id=creator.id,
            is_active=True,
        )
        db.add(league)
        await db.flush()

        membership = LeagueMembership(
            id=uuid.uuid4(),
            user_id=creator.id,
            league_id=league.id,
            role="creator",
        )
        db.add(membership)
        await db.flush()

        joiner = User(
            id=uuid.uuid4(),
            username="case_joiner",
            email="case_joiner@test.com",
            is_active=True,
        )
        db.add(joiner)
        await db.flush()

        async def override_get_current_user():
            return joiner

        app.dependency_overrides[get_current_user] = override_get_current_user

        # Try joining with lowercase
        response = await client.post(
            "/leagues/join",
            json={"code": "casetest"},
        )

        # This will fail because codes are uppercase and case-sensitive
        assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_response_includes_all_required_fields(self, client, db):
        """League response includes all required fields."""
        user = User(
            id=uuid.uuid4(),
            username="field_user",
            email="field@test.com",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.commit()

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.post(
                "/leagues",
                json={"name": "Field Test League"},
            )

            assert response.status_code == 201
            data = response.json()

            # Check all required fields
            required_fields = [
                "id",
                "name",
                "code",
                "creator_id",
                "is_active",
                "created_at",
                "updated_at",
            ]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"

            # Timestamp fields should be strings (ISO format)
            assert isinstance(data["created_at"], str)
            assert isinstance(data["updated_at"], str)
        finally:
            app.dependency_overrides.clear()
