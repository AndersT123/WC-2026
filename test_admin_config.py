"""Test admin configuration without running server."""
import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_admin_configuration():
    """Test that admin configuration is properly set up."""
    print("=" * 70)
    print("Testing Admin Configuration Setup")
    print("=" * 70)

    # Test 1: Check config loads without errors
    print("\n1. Testing configuration loading...")
    try:
        from app.config import settings
        print(f"   ✓ Config loaded successfully")
        print(f"   Admin emails string: {settings.admin_emails_str}")
        print(f"   Admin emails property: {settings.admin_emails}")
    except Exception as e:
        print(f"   ✗ Error loading config: {e}")
        return False

    # Test 2: Check admin_emails property parsing
    print("\n2. Testing admin_emails parsing...")
    if "andertvistholm@live.dk" in settings.admin_emails:
        print(f"   ✓ Admin email correctly parsed")
    else:
        print(f"   ✗ Admin email not found in list")
        print(f"   Expected: ['andertvistholm@live.dk']")
        print(f"   Got: {settings.admin_emails}")
        return False

    # Test 3: Check exceptions are defined
    print("\n3. Testing ForbiddenError exception...")
    try:
        from app.exceptions import ForbiddenError
        from fastapi import status

        error = ForbiddenError("Test error")
        if error.status_code == status.HTTP_403_FORBIDDEN:
            print(f"   ✓ ForbiddenError correctly configured (status 403)")
        else:
            print(f"   ✗ ForbiddenError has wrong status code: {error.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error with ForbiddenError: {e}")
        return False

    # Test 4: Check dependencies are defined
    print("\n4. Testing get_admin_user dependency...")
    try:
        from app.dependencies import get_admin_user
        print(f"   ✓ get_admin_user dependency exists")
    except Exception as e:
        print(f"   ✗ Error importing get_admin_user: {e}")
        return False

    # Test 5: Check match schemas
    print("\n5. Testing UpdateMatchResultRequest schema...")
    try:
        from app.schemas.match import UpdateMatchResultRequest

        # Test valid request
        request = UpdateMatchResultRequest(home_score=2, away_score=1, status="completed")
        print(f"   ✓ Valid request created: {request}")

        # Test validation - negative scores should fail
        try:
            bad_request = UpdateMatchResultRequest(home_score=-1, away_score=1)
            print(f"   ✗ Negative scores were accepted (should be rejected)")
            return False
        except Exception:
            print(f"   ✓ Negative scores correctly rejected")

        # Test validation - invalid status should fail
        try:
            bad_request = UpdateMatchResultRequest(home_score=1, away_score=1, status="invalid")
            print(f"   ✗ Invalid status was accepted (should be rejected)")
            return False
        except Exception:
            print(f"   ✓ Invalid status correctly rejected")

    except Exception as e:
        print(f"   ✗ Error with UpdateMatchResultRequest: {e}")
        return False

    # Test 6: Check match service function
    print("\n6. Testing update_match_result service function...")
    try:
        from app.services.match_service import update_match_result
        print(f"   ✓ update_match_result function exists")
    except Exception as e:
        print(f"   ✗ Error importing update_match_result: {e}")
        return False

    # Test 7: Check matches router has the new endpoint
    print("\n7. Testing matches router has PUT endpoint...")
    try:
        from app.routers import matches as matches_router

        # Check if the router has the update_match_result_endpoint
        endpoint_found = False
        for route in matches_router.router.routes:
            if hasattr(route, 'path') and '/{match_id}/result' in route.path:
                if hasattr(route, 'methods') and 'PUT' in route.methods:
                    endpoint_found = True
                    print(f"   ✓ PUT /{'{match_id}/result'} endpoint found")
                    break

        if not endpoint_found:
            print(f"   ✗ PUT endpoint not found in router")
            print(f"   Available routes:")
            for route in matches_router.router.routes:
                if hasattr(route, 'path'):
                    methods = getattr(route, 'methods', ['GET'])
                    print(f"      {methods}: {route.path}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking router: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("✓ All configuration tests passed!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_admin_configuration())
    sys.exit(0 if result else 1)
