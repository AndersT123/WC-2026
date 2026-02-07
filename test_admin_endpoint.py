"""Test admin endpoint for updating match results and calculating prediction points."""
import asyncio
import httpx
import uuid
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080"

async def create_test_data_directly():
    """Create test match and prediction directly in database without ORM issues."""
    import sqlite3

    conn = sqlite3.connect("worldcup.db")
    cursor = conn.cursor()

    try:
        # Get admin user ID
        cursor.execute("SELECT id FROM users WHERE email = ?", ("andertvistholm@live.dk",))
        result = cursor.fetchone()
        if not result:
            print("   Admin user not found in database")
            return None, None

        admin_user_id = result[0]
        match_id = str(uuid.uuid4())
        prediction_id = str(uuid.uuid4())
        league_id = str(uuid.uuid4())

        # Create league
        cursor.execute(
            "INSERT INTO leagues (id, name, code, creator_id, is_active) VALUES (?, ?, ?, ?, ?)",
            (league_id, "Test League", "TEST", admin_user_id, True)
        )

        # Add user to league
        cursor.execute(
            "INSERT INTO league_memberships (id, user_id, league_id) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), admin_user_id, league_id)
        )

        # Create match
        cursor.execute(
            """INSERT INTO matches
               (id, home_team, away_team, match_datetime, venue, status, home_score, away_score, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (match_id, "Test Home", "Test Away",
             (datetime.utcnow() + timedelta(hours=1)).isoformat(), "Test Stadium",
             "scheduled", None, None,
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
        )

        # Create prediction
        cursor.execute(
            """INSERT INTO predictions
               (id, user_id, match_id, league_id, home_score, away_score, points_earned, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (prediction_id, admin_user_id, match_id, league_id, 2, 1, None,
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
        )

        conn.commit()
        print(f"   ✓ Created test data")
        print(f"     League ID: {league_id}")
        print(f"     Match ID: {match_id}")
        print(f"     Prediction ID: {prediction_id}")

        return match_id, prediction_id
    finally:
        conn.close()

async def verify_prediction_scored(prediction_id):
    """Check if prediction was scored."""
    import sqlite3

    conn = sqlite3.connect("worldcup.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT points_earned FROM predictions WHERE id = ?", (prediction_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    finally:
        conn.close()

async def main():
    print("=" * 70)
    print("Testing Admin Endpoint: Update Match Result")
    print("=" * 70)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        email = "andertvistholm@live.dk"

        # Step 1: Signup the admin user
        print("\n1. Setting up admin user...")
        username = f"admin_{int(time.time())}"

        response = await client.post(
            f"{BASE_URL}/auth/signup",
            json={"username": username, "email": email}
        )
        print(f"   Signup response: {response.status_code}")

        if response.status_code not in [200, 409]:
            print(f"   Error: {response.text}")
            return

        # Get token from database
        import sqlite3
        conn = sqlite3.connect("worldcup.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT token FROM magic_link_tokens WHERE email = ? ORDER BY created_at DESC LIMIT 1",
            (email,)
        )
        token_result = cursor.fetchone()
        conn.close()

        if not token_result:
            print("   No magic link token found")
            return

        token = token_result[0]
        print(f"   Token retrieved: {token[:20]}...")

        # Step 2: Verify token and authenticate
        print("\n2. Authenticating with magic link...")
        response = await client.get(
            f"{BASE_URL}/auth/verify",
            params={"token": token, "username": username}
        )
        print(f"   Authentication: {response.status_code}")

        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return

        print(f"   ✓ Authenticated as {email}")

        # Step 3: Create test data
        print("\n3. Creating test data (match and prediction)...")
        match_id, prediction_id = await create_test_data_directly()

        if not match_id:
            print("   Failed to create test data")
            return

        # Step 4: Test the admin endpoint
        print("\n4. Testing PUT /matches/{match_id}/result endpoint...")
        print(f"   URL: PUT {BASE_URL}/matches/{match_id}/result")

        request_body = {
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }
        print(f"   Request body: {request_body}")

        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json=request_body
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Success!")
            print(f"   Match updated:")
            print(f"     - Home Score: {result['home_score']}")
            print(f"     - Away Score: {result['away_score']}")
            print(f"     - Status: {result['status']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.json()}")
            return

        # Step 5: Verify prediction was scored
        print("\n5. Verifying prediction was scored...")
        points = await verify_prediction_scored(prediction_id)

        if points is not None:
            print(f"   Prediction points earned: {points}")
            print(f"   ✓ Prediction was scored!")
        else:
            print(f"   ✗ Prediction was not scored")

        # Step 6: Test error cases
        print("\n6. Testing error cases...")

        # Test 6a: Invalid match ID (404)
        print("\n   6a. Testing invalid match ID (should return 404)...")
        invalid_id = uuid.uuid4()
        response = await client.put(
            f"{BASE_URL}/matches/{invalid_id}/result",
            json=request_body
        )
        print(f"       Status: {response.status_code}")
        if response.status_code == 404:
            print(f"       ✓ Correct error code")
        else:
            print(f"       ✗ Expected 404, got {response.status_code}")

        # Test 6b: Invalid request data - negative scores (422)
        print("\n   6b. Testing invalid scores - negative values (should return 422)...")
        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json={"home_score": -1, "away_score": 1, "status": "completed"}
        )
        print(f"       Status: {response.status_code}")
        if response.status_code == 422:
            print(f"       ✓ Correct error code")
        else:
            print(f"       ✗ Expected 422, got {response.status_code}")

        # Test 6c: Invalid status (422)
        print("\n   6c. Testing invalid status (should return 422)...")
        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json={"home_score": 1, "away_score": 1, "status": "invalid_status"}
        )
        print(f"       Status: {response.status_code}")
        if response.status_code == 422:
            print(f"       ✓ Correct error code")
        else:
            print(f"       ✗ Expected 422, got {response.status_code}")

        # Test 6d: Test with non-admin user (403)
        print("\n   6d. Testing access with non-admin user (should return 403)...")

        # Logout current user
        await client.post(f"{BASE_URL}/auth/logout")

        # Create and authenticate as non-admin user
        non_admin_username = f"user_{int(time.time())}"
        non_admin_email = f"user_{int(time.time())}@example.com"

        response = await client.post(
            f"{BASE_URL}/auth/signup",
            json={"username": non_admin_username, "email": non_admin_email}
        )

        conn = sqlite3.connect("worldcup.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT token FROM magic_link_tokens WHERE email = ? ORDER BY created_at DESC LIMIT 1",
            (non_admin_email,)
        )
        token_result = cursor.fetchone()
        conn.close()

        if token_result:
            token = token_result[0]
            response = await client.get(
                f"{BASE_URL}/auth/verify",
                params={"token": token, "username": non_admin_username}
            )

        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json=request_body
        )
        print(f"       Status: {response.status_code}")
        if response.status_code == 403:
            print(f"       ✓ Correct error code - non-admin blocked")
        else:
            print(f"       ✗ Expected 403, got {response.status_code}")

    print("\n" + "=" * 70)
    print("✓ Admin endpoint tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
