"""Quick test script to verify the application works."""
import asyncio
import sys

async def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing imports...")
        from app.main import app
        from app.config import settings
        from app.database import Base
        from app.models.user import User, MagicLinkToken
        from app.services import auth_service, token_service, email_service
        from app.routers import auth, health
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database():
    """Test database initialization."""
    try:
        print("\nTesting database...")
        from app.database import init_db
        await init_db()
        print("✓ Database initialization successful")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Application Tests")
    print("=" * 60)

    results = []
    results.append(await test_imports())
    results.append(await test_database())

    print("\n" + "=" * 60)
    if all(results):
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
