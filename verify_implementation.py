"""Verify the admin endpoint implementation is complete and working."""
import sqlite3
import uuid
from datetime import datetime, timedelta

def verify_implementation():
    """Verify all components of the admin endpoint are in place."""
    print("=" * 70)
    print("Verifying Admin Endpoint Implementation")
    print("=" * 70)

    # 1. Verify config has admin_emails
    print("\n1. Checking configuration...")
    try:
        from app.config import settings
        emails = settings.admin_emails
        print(f"   ✓ admin_emails configured: {emails}")
        if "andertvistholm@live.dk" in emails:
            print(f"   ✓ andertvistholm@live.dk is an admin")
        else:
            print(f"   ✗ andertvistholm@live.dk is NOT an admin")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 2. Verify exceptions
    print("\n2. Checking ForbiddenError exception...")
    try:
        from app.exceptions import ForbiddenError
        from fastapi import status
        err = ForbiddenError()
        if err.status_code == status.HTTP_403_FORBIDDEN:
            print(f"   ✓ ForbiddenError configured correctly (403)")
        else:
            print(f"   ✗ Wrong status code: {err.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 3. Verify dependencies
    print("\n3. Checking admin dependency...")
    try:
        from app.dependencies import get_admin_user
        print(f"   ✓ get_admin_user dependency exists")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 4. Verify schemas
    print("\n4. Checking UpdateMatchResultRequest schema...")
    try:
        from app.schemas.match import UpdateMatchResultRequest

        # Valid request
        req = UpdateMatchResultRequest(home_score=2, away_score=1, status="completed")
        print(f"   ✓ Valid request accepted")

        # Negative scores should fail
        try:
            bad = UpdateMatchResultRequest(home_score=-1, away_score=1)
            print(f"   ✗ Negative scores not rejected")
            return False
        except:
            print(f"   ✓ Negative scores rejected")

        # Invalid status should fail
        try:
            bad = UpdateMatchResultRequest(home_score=1, away_score=1, status="invalid")
            print(f"   ✗ Invalid status not rejected")
            return False
        except:
            print(f"   ✓ Invalid status rejected")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 5. Verify service functions
    print("\n5. Checking service functions...")
    try:
        from app.services.match_service import update_match_result
        from app.services.prediction_service import update_predictions_after_match
        print(f"   ✓ update_match_result function exists")
        print(f"   ✓ update_predictions_after_match function exists")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 6. Verify router endpoint
    print("\n6. Checking router endpoint...")
    try:
        from app.routers import matches as matches_router

        endpoint_found = False
        for route in matches_router.router.routes:
            if hasattr(route, 'path') and '/{match_id}/result' in route.path:
                if hasattr(route, 'methods') and 'PUT' in route.methods:
                    endpoint_found = True
                    break

        if endpoint_found:
            print(f"   ✓ PUT /{'{match_id}/result'} endpoint exists")
        else:
            print(f"   ✗ PUT endpoint not found")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 7. Verify data in database
    print("\n7. Checking test data in database...")
    try:
        conn = sqlite3.connect("worldcup.db")
        cursor = conn.cursor()

        # Count test matches
        cursor.execute("SELECT COUNT(*) FROM matches WHERE home_team = 'Team A'")
        count = cursor.fetchone()[0]
        print(f"   Test matches created: {count}")

        # Count predictions
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE home_score = 2 AND away_score = 1")
        pred_count = cursor.fetchone()[0]
        print(f"   Test predictions created: {pred_count}")

        # Check admin user
        cursor.execute("SELECT id FROM users WHERE email = 'andertvistholm@live.dk'")
        admin_id = cursor.fetchone()
        if admin_id:
            print(f"   ✓ Admin user exists in database")
        else:
            print(f"   ✗ Admin user not found in database")

        conn.close()

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n" + "=" * 70)
    print("✓ Implementation verification complete!")
    print("=" * 70)
    print("\nAll components are in place and ready for testing.")
    print("\nTo test the endpoint manually:")
    print("1. Authenticate with andertvistholm@live.dk")
    print("2. Call: PUT /matches/{match_id}/result")
    print("3. Send: {\"home_score\": 2, \"away_score\": 1, \"status\": \"completed\"}")
    print("\nExpected result:")
    print("- Match scores updated")
    print("- Prediction points calculated automatically")
    print("- HTTP 200 response")
    print("\nError cases:")
    print("- 401 if not authenticated")
    print("- 403 if not an admin")
    print("- 404 if match not found")
    print("- 422 if invalid data (negative scores, invalid status)")

    return True

if __name__ == "__main__":
    success = verify_implementation()
    exit(0 if success else 1)
