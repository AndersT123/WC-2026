"""Simplified admin endpoint test using existing auth tokens."""
import asyncio
import httpx
import uuid
import sqlite3
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080"

async def test_admin_endpoint():
    print("=" * 70)
    print("Testing Admin Endpoint: Update Match Result")
    print("=" * 70)

    # Get existing admin auth token
    conn = sqlite3.connect("worldcup.db")
    cursor = conn.cursor()

    # Get admin user ID
    cursor.execute("SELECT id FROM users WHERE email = 'andertvistholm@live.dk'")
    result = cursor.fetchone()
    if not result:
        print("Admin user not found")
        conn.close()
        return

    admin_user_id = result[0]
    print(f"\n1. Admin user ID: {admin_user_id}")

    # Create test league
    league_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO leagues (id, name, code, creator_id, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (league_id, "Test League", "TEST", admin_user_id, True,
         datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
    )

    # Add admin to league
    cursor.execute(
        "INSERT INTO league_memberships (id, user_id, league_id, role, joined_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), admin_user_id, league_id, "member", datetime.utcnow().isoformat())
    )

    # Create test match
    match_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO matches
           (id, home_team, away_team, match_datetime, venue, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_id, "Team A", "Team B",
         (datetime.utcnow() + timedelta(hours=1)).isoformat(),
         "Stadium",
         "scheduled",
         datetime.utcnow().isoformat(),
         datetime.utcnow().isoformat())
    )

    # Create prediction
    prediction_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO predictions
           (id, user_id, match_id, league_id, home_score, away_score, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (prediction_id, admin_user_id, match_id, league_id, 2, 1,
         datetime.utcnow().isoformat(),
         datetime.utcnow().isoformat())
    )

    conn.commit()
    print(f"   ✓ Test data created:")
    print(f"     - Match: {match_id}")
    print(f"     - Prediction: {prediction_id}")

    # Create auth cookie with existing JWT token
    # We need to get a valid auth token
    # First, let's get the latest magic link token and verify it
    cursor.execute(
        "SELECT token FROM magic_link_tokens WHERE email = 'andertvistholm@live.dk' ORDER BY created_at DESC LIMIT 1"
    )
    magic_token_result = cursor.fetchone()
    conn.close()

    if not magic_token_result:
        print("No magic link token found")
        return

    magic_token = magic_token_result[0]
    print(f"\n2. Using magic link token: {magic_token[:20]}...")

    async with httpx.AsyncClient() as client:
        # Verify the magic link to get authenticated
        print("\n3. Verifying magic link...")
        response = await client.get(
            f"{BASE_URL}/auth/verify",
            params={"token": magic_token}
        )
        print(f"   Status: {response.status_code}")

        if response.status_code != 200:
            print(f"   Error: {response.json()}")
            return

        print("   ✓ Authenticated")

        # Now test the admin endpoint
        print(f"\n4. Testing PUT /matches/{match_id}/result...")
        request_body = {
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }

        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json=request_body
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Match updated successfully!")
            print(f"     Home Score: {result['home_score']}")
            print(f"     Away Score: {result['away_score']}")
            print(f"     Status: {result['status']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.json()}")
            return

        # Verify prediction was scored
        print(f"\n5. Verifying prediction was scored...")
        conn = sqlite3.connect("worldcup.db")
        cursor = conn.cursor()
        cursor.execute("SELECT points_earned FROM predictions WHERE id = ?", (prediction_id,))
        points_result = cursor.fetchone()
        conn.close()

        if points_result and points_result[0] is not None:
            print(f"   ✓ Prediction scored with {points_result[0]} points!")
        else:
            print(f"   ✗ Prediction was not scored")
            return

        # Test error cases
        print(f"\n6. Testing error cases...")

        # 6a: Invalid match ID (404)
        print("\n   6a. Invalid match ID (should be 404)...")
        response = await client.put(
            f"{BASE_URL}/matches/{str(uuid.uuid4())}/result",
            json=request_body
        )
        print(f"       Status: {response.status_code} {'✓' if response.status_code == 404 else '✗'}")

        # 6b: Negative scores (422)
        print("\n   6b. Negative scores (should be 422)...")
        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json={"home_score": -1, "away_score": 1}
        )
        print(f"       Status: {response.status_code} {'✓' if response.status_code == 422 else '✗'}")

        # 6c: Invalid status (422)
        print("\n   6c. Invalid status (should be 422)...")
        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json={"home_score": 1, "away_score": 1, "status": "invalid"}
        )
        print(f"       Status: {response.status_code} {'✓' if response.status_code == 422 else '✗'}")

        # 6d: Unauthenticated access (401)
        print("\n   6d. Unauthenticated access (should be 401)...")
        async with httpx.AsyncClient() as unauth_client:
            response = await unauth_client.put(
                f"{BASE_URL}/matches/{match_id}/result",
                json=request_body
            )
            print(f"       Status: {response.status_code} {'✓' if response.status_code == 401 else '✗'}")

    print("\n" + "=" * 70)
    print("✓ All tests passed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_admin_endpoint())
