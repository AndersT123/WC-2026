"""Final admin endpoint test with fresh authentication."""
import asyncio
import httpx
import uuid
import sqlite3
import time
from datetime import datetime, timedelta
import random
import string

BASE_URL = "http://localhost:8080"

async def test_admin_endpoint():
    print("=" * 70)
    print("Testing Admin Endpoint: Update Match Result")
    print("=" * 70)

    conn = sqlite3.connect("worldcup.db")
    cursor = conn.cursor()

    # Get admin user ID
    cursor.execute("SELECT id FROM users WHERE email = 'andertvistholm@live.dk'")
    admin_user_id = cursor.fetchone()[0]
    print(f"\n1. Admin user ID: {admin_user_id}")

    # Create test data - use UUID objects that get converted to strings properly
    league_id_obj = uuid.uuid4()
    league_id = str(league_id_obj)
    admin_user_id_str = str(admin_user_id)  # Ensure admin_user_id is a string
    league_code = ''.join(random.choices(string.ascii_uppercase, k=4))
    cursor.execute(
        "INSERT INTO leagues (id, name, code, creator_id, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (league_id, "Test League", league_code, admin_user_id_str, True,
         datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
    )

    cursor.execute(
        "INSERT INTO league_memberships (id, user_id, league_id, role, joined_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), admin_user_id_str, league_id, "member", datetime.utcnow().isoformat())
    )

    match_id_obj = uuid.uuid4()
    match_id = str(match_id_obj)
    cursor.execute(
        """INSERT INTO matches
           (id, home_team, away_team, match_datetime, venue, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_id, "Team A", "Team B",
         (datetime.utcnow() + timedelta(hours=1)).isoformat(),
         "Stadium", "scheduled",
         datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
    )

    prediction_id_obj = uuid.uuid4()
    prediction_id = str(prediction_id_obj)
    cursor.execute(
        """INSERT INTO predictions
           (id, user_id, match_id, league_id, home_score, away_score, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (prediction_id, admin_user_id, match_id, league_id, 2, 1,
         datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
    )

    conn.commit()
    print(f"   ✓ Test data created:")
    print(f"     - Match: {match_id}")
    print(f"     - Prediction: {prediction_id}")

    # Request a fresh magic link
    async with httpx.AsyncClient() as client:
        print(f"\n2. Requesting fresh magic link...")
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "andertvistholm@live.dk"}
        )
        print(f"   Status: {response.status_code}")

        if response.status_code != 200:
            print(f"   Error: {response.json()}")
            return

        # Get the fresh token
        cursor.execute(
            "SELECT token FROM magic_link_tokens WHERE email = 'andertvistholm@live.dk' AND used_at IS NULL ORDER BY created_at DESC LIMIT 1"
        )
        magic_token_result = cursor.fetchone()
        conn.close()

        if not magic_token_result:
            print("   No unused magic link token found")
            return

        magic_token = magic_token_result[0]
        print(f"   ✓ Fresh token: {magic_token[:20]}...")

        # Authenticate
        print(f"\n3. Authenticating with magic link...")
        response = await client.get(
            f"{BASE_URL}/auth/verify",
            params={"token": magic_token}
        )
        print(f"   Status: {response.status_code}")

        if response.status_code != 200:
            print(f"   Error: {response.json()}")
            return

        print("   ✓ Authenticated")

        # First, test if GET works for the match
        print(f"\n4a. Testing GET /matches/{match_id}...")
        response = await client.get(f"{BASE_URL}/matches/{match_id}")
        print(f"    Status: {response.status_code}")
        if response.status_code != 200:
            print(f"    Error: {response.json()}")
            return
        else:
            print(f"    ✓ GET works, match found")

        # Test the admin endpoint
        print(f"\n4b. Testing PUT /matches/{match_id}/result...")
        request_body = {
            "home_score": 2,
            "away_score": 1,
            "status": "completed"
        }

        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json=request_body
        )

        print(f"    Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"    ✓ Match updated successfully!")
            print(f"      - Home Score: {result['home_score']}")
            print(f"      - Away Score: {result['away_score']}")
            print(f"      - Status: {result['status']}")
        else:
            print(f"    ✗ Error: {response.status_code}")
            print(f"    Response: {response.json()}")
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
        status_ok = response.status_code == 404
        print(f"       Status: {response.status_code} {'✓' if status_ok else '✗ (expected 404)'}")

        # 6b: Negative scores (422)
        print("\n   6b. Negative scores (should be 422)...")
        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json={"home_score": -1, "away_score": 1}
        )
        status_ok = response.status_code == 422
        print(f"       Status: {response.status_code} {'✓' if status_ok else '✗ (expected 422)'}")

        # 6c: Invalid status (422)
        print("\n   6c. Invalid status (should be 422)...")
        response = await client.put(
            f"{BASE_URL}/matches/{match_id}/result",
            json={"home_score": 1, "away_score": 1, "status": "invalid"}
        )
        status_ok = response.status_code == 422
        print(f"       Status: {response.status_code} {'✓' if status_ok else '✗ (expected 422)'}")

        # 6d: Unauthenticated access (401)
        print("\n   6d. Unauthenticated access (should be 401)...")
        async with httpx.AsyncClient() as unauth_client:
            response = await unauth_client.put(
                f"{BASE_URL}/matches/{match_id}/result",
                json=request_body
            )
            status_ok = response.status_code == 401
            print(f"       Status: {response.status_code} {'✓' if status_ok else '✗ (expected 401)'}")

    print("\n" + "=" * 70)
    print("✓ Admin endpoint tests completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_admin_endpoint())
