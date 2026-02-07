"""Test authentication endpoints with proper cookie handling."""
import asyncio
import httpx

BASE_URL = "http://localhost:8080"

async def main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=" * 60)
        print("Testing Magic Link Authentication")
        print("=" * 60)

        # Test 1: Signup
        import time
        username = f"testuser{int(time.time())}"
        email = "anderstvistholm@live.dk"

        print("\n1. Testing signup...")
        response = await client.post(
            f"{BASE_URL}/auth/signup",
            json={"username": username, "email": email}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # Get the token from database
        from app.database import async_session_maker
        from app.models.user import MagicLinkToken
        from sqlalchemy import select

        async with async_session_maker() as db:
            result = await db.execute(
                select(MagicLinkToken)
                .order_by(MagicLinkToken.created_at.desc())
                .limit(1)
            )
            token_obj = result.scalar_one()
            token = token_obj.token
            print(f"Generated token: {token[:20]}...")

        # Test 2: Verify magic link (signup)
        print("\n2. Testing magic link verification (signup)...")
        response = await client.get(
            f"{BASE_URL}/auth/verify",
            params={"token": token, "username": username}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print(f"Cookies set: {dict(response.cookies)}")

        # Test 3: Access protected endpoint
        print("\n3. Testing protected endpoint (/auth/me)...")
        response = await client.get(f"{BASE_URL}/auth/me")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print("✓ Authentication working!")
        else:
            print(f"Response: {response.json()}")
            print("✗ Authentication failed")

        # Test 4: Login flow
        print("\n4. Testing login flow...")
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")

        # Get new token
        async with async_session_maker() as db:
            result = await db.execute(
                select(MagicLinkToken)
                .order_by(MagicLinkToken.created_at.desc())
                .limit(1)
            )
            token_obj = result.scalar_one()
            token = token_obj.token

        # Verify login token
        print("\n5. Testing magic link verification (login)...")
        response = await client.get(
            f"{BASE_URL}/auth/verify",
            params={"token": token}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test 6: Logout
        print("\n6. Testing logout...")
        response = await client.post(f"{BASE_URL}/auth/logout")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test 7: Access protected endpoint after logout
        print("\n7. Testing protected endpoint after logout...")
        response = await client.get(f"{BASE_URL}/auth/me")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Logout working - access denied as expected")
        else:
            print("✗ Logout failed - still authenticated")

        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
