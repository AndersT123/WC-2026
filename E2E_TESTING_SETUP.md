# E2E Testing Setup - Complete Guide

## Overview

The E2E testing framework is fully configured and ready to use. It includes:

1. **Test Data Seeder** - Creates test users, leagues, matches, and predictions directly in the database
2. **Automated Test Suite** - 7 comprehensive test scenarios using pytest
3. **Quick Start Script** - One-command execution of the entire test pipeline
4. **Documentation** - Complete guides for users and developers

---

## Quick Start (30 seconds)

### Option 1: Automated Quick Start Script

```bash
cd /home/anders/hello-scaleway
bash run_e2e_tests.sh
```

This will:
1. Clean the database
2. Seed test data
3. Optionally start the backend
4. Run all 7 test scenarios
5. Clean up
6. Display results

### Option 2: Manual Steps

```bash
# 1. Seed test data
python3 scripts/seed_test_data.py

# 2. Start backend (in another terminal)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# 3. Run tests
pytest tests/test_e2e_scenarios.py -v
```

---

## What's Included

### 1. Test Data Seeding (`scripts/seed_test_data.py`)

Creates a complete testing environment with:

**Test Users:**
- alice (alice@test.com) - creator of league 1
- bob (bob@test.com) - creator of league 2
- charlie (charlie@test.com) - member of league 1
- diana (diana@test.com) - member of league 2

**Leagues:**
- Test League 1 (TEST0001) - alice, bob, charlie
- Test League 2 (TEST0002) - bob, alice, diana

**Matches:**
- 1 completed match (Team A vs Team B, 2-1)
- 3 scheduled matches (upcoming)

**Predictions:**
- 3 predictions for completed match (with calculated points)
- 8 predictions for upcoming matches

**Magic Link Tokens:**
- Auto-generated for each test user (simulates login without email)

**Run it:**
```bash
python3 scripts/seed_test_data.py
```

### 2. Test Suite (`tests/test_e2e_scenarios.py`)

Seven comprehensive test scenarios:

| # | Test | Description |
|---|------|-------------|
| 1 | `test_scenario_1_login_and_create_league` | User logs in and creates a new league |
| 2 | `test_scenario_2_login_and_join_league` | User joins existing league with code |
| 3 | `test_scenario_3_set_predictions_different_users` | Multiple users make predictions |
| 4 | `test_scenario_4_admin_update_results` | Admin updates match scores/status |
| 5 | `test_scenario_5_witt_classic_scoring` | Validates all 5 scoring rules |
| 6 | `test_scenario_6_league_standings_updated` | Leaderboard calculation correct |
| Bonus | `test_complete_workflow` | Full end-to-end integration test |

**Run specific test:**
```bash
pytest tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_1_login_and_create_league -v
```

**Run all tests with output:**
```bash
pytest tests/test_e2e_scenarios.py -v -s
```

### 3. Quick Start Script (`run_e2e_tests.sh`)

Automated test execution with:
- Database cleanup
- Data seeding
- Optional backend startup
- Test execution
- Backend cleanup
- Results summary

**Run it:**
```bash
bash run_e2e_tests.sh
```

### 4. Configuration (`pytest.ini`)

Pytest configuration for proper module loading:
- Sets Python path
- Enables async test support
- Configures test discovery

---

## Test Data Details

### Users and Leagues

```
Username    | Email              | League 1       | League 2
------------|--------------------|--------------------|----------
alice       | alice@test.com      | creator       | member
bob         | bob@test.com        | member        | creator
charlie     | charlie@test.com    | member        | -
diana       | diana@test.com      | -             | member
```

### Scoring Validation (Test Scenario 5)

The test verifies all Witt-Classic scoring rules:

```
Prediction       | Actual  | Result      | Points
-----------------|---------|-------------|--------
2-1              | 2-1     | Exact match | 5
2-0              | 2-1     | Winner + 1  | 3
1-1              | 2-1     | Wrong       | 1
2-2              | 2-1     | One score   | 1
```

### Leaderboard Validation (Test Scenario 6)

After match completion, standings should show:
- alice: 5 points (🥇)
- bob: 3 points (🥈)
- charlie: 1 point (🥉)

---

## Database Verification

After seeding, verify the database contains all test data:

```python
# Use Python to check database
python3 << 'EOF'
import sqlite3

conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()

# Check users
cursor.execute("SELECT COUNT(*) FROM users WHERE email LIKE '%test.com%'")
print(f"Test users: {cursor.fetchone()[0]}")

# Check leagues
cursor.execute("SELECT COUNT(*) FROM leagues WHERE code LIKE 'TEST%'")
print(f"Test leagues: {cursor.fetchone()[0]}")

# Check memberships
cursor.execute("SELECT COUNT(*) FROM league_memberships")
print(f"League memberships: {cursor.fetchone()[0]}")

# Check matches
cursor.execute("SELECT COUNT(*) FROM matches")
print(f"Matches: {cursor.fetchone()[0]}")

# Check predictions with points
cursor.execute("SELECT COUNT(*) FROM predictions WHERE points_earned IS NOT NULL")
print(f"Predictions with points: {cursor.fetchone()[0]}")

conn.close()
EOF
```

Expected output:
```
Test users: 4
Test leagues: 2
League memberships: 6
Matches: 4
Predictions with points: 3
```

---

## API Endpoints Tested

### Authentication
- `GET /auth/me` - Get current user info
- `POST /auth/login` - Login (simulated via tokens)

### Leagues
- `POST /leagues/` - Create new league
- `GET /leagues/` - Get user's leagues
- `POST /leagues/join` - Join league by code

### Matches
- `GET /matches/` - Get all matches
- `PUT /matches/{id}/result` - Update match result (admin only)

### Predictions
- `POST /predictions/` - Create prediction
- `GET /predictions/league/{league_id}/leaderboard` - Get league standings

---

## Admin Endpoint Testing

The admin endpoint update is tested in `test_scenario_4_admin_update_results`:

1. **Admin Email Setup**: Uses `andertvistholm@live.dk` from `.env`
2. **Match Update**: Updates match score and status
3. **Point Calculation**: Triggers automatic point calculation
4. **Verification**: Confirms predictions are scored

**Manual test:**
```bash
# Update match result (requires admin email in ADMIN_EMAILS_STR)
curl -X PUT "http://localhost:8080/matches/{match_id}/result" \
  -H "Content-Type: application/json" \
  -d '{"home_score": 2, "away_score": 1, "status": "completed"}' \
  -b "access_token=YOUR_TOKEN"
```

---

## Test Execution Flow

### Phase 1: Setup
```
1. Create database schema
2. Seed test users, leagues, matches
3. Create magic link tokens for test users
4. Calculate points for completed matches
```

### Phase 2: Run Tests
```
1. Load test users from database
2. For each scenario:
   a. Setup test data
   b. Execute API calls
   c. Verify database state
   d. Assert expected results
3. Generate test report
```

### Phase 3: Cleanup
```
1. Remove test database
2. Stop backend if running
3. Display results summary
```

---

## Expected Test Results

All tests should **PASS** ✅

```
test_scenario_1_login_and_create_league PASSED
test_scenario_2_login_and_join_league PASSED
test_scenario_3_set_predictions_different_users PASSED
test_scenario_4_admin_update_results PASSED
test_scenario_5_witt_classic_scoring PASSED
test_scenario_6_league_standings_updated PASSED
test_complete_workflow PASSED

============== 7 passed in X.XXs ==============
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution**: Ensure `pytest.ini` exists in the project root with correct `pythonpath`.

```bash
# Verify pytest.ini exists
ls -la pytest.ini

# Or run with PYTHONPATH
PYTHONPATH=/home/anders/hello-scaleway pytest tests/test_e2e_scenarios.py -v
```

### Issue: "Database locked"

**Solution**: Close any existing database connections.

```bash
# Remove the database and reseed
rm -f worldcup.db
python3 scripts/seed_test_data.py
```

### Issue: "Backend connection refused"

**Solution**: Make sure backend is running before running tests.

```bash
# Check if backend is running
curl http://localhost:8080/health

# If not, start it
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Issue: Tests fail with authentication errors

**Solution**: Verify magic link tokens exist in database.

```python
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()
cursor.execute("SELECT email, token FROM magic_link_tokens WHERE email LIKE '%test.com%'")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1][:30]}...")
conn.close()
EOF
```

---

## Files and Locations

```
/home/anders/hello-scaleway/
├── scripts/
│   └── seed_test_data.py           ← Test data seeder
├── tests/
│   └── test_e2e_scenarios.py        ← Main test suite
├── run_e2e_tests.sh                 ← Quick start script
├── pytest.ini                       ← Pytest config
├── E2E_TESTING_GUIDE.md             ← Detailed guide
├── E2E_TESTING_SETUP.md             ← This file
├── worldcup.db                      ← Test database (auto-created)
└── .env                             ← Config with admin email
```

---

## Configuration

### .env File

Must include admin email for test scenario 4:

```env
ADMIN_EMAILS_STR=andertvistholm@live.dk
```

### pytest.ini

Already configured with:
- Python path
- Async mode
- Test discovery

---

## Running Tests in CI/CD

The test suite is designed to be CI/CD friendly:

```bash
#!/bin/bash
set -e

# Navigate to project
cd /home/anders/hello-scaleway

# Run tests (assumes dependencies are installed)
python3 scripts/seed_test_data.py
python3 -m uvicorn app.main:app --port 8080 &
sleep 3

pytest tests/test_e2e_scenarios.py -v --tb=short

# Kill backend
pkill -f uvicorn
```

---

## Summary

✅ **Test Data Seeding**: Fully automated with 4 users, 2 leagues, 4 matches
✅ **Test Suite**: 7 comprehensive scenarios covering all features
✅ **Quick Start**: One-command execution with `bash run_e2e_tests.sh`
✅ **Configuration**: Minimal setup required, pytest.ini handles paths
✅ **Documentation**: Complete guides for users and developers

### Next Steps

1. **Run the seeder**: `python3 scripts/seed_test_data.py`
2. **Verify database**: Check test data is created
3. **Run tests**: `pytest tests/test_e2e_scenarios.py -v`
4. **Check results**: All 7 tests should pass

### Status

🚀 **E2E Testing Framework: READY FOR USE**

All components are implemented, configured, and tested. The framework is production-ready and can validate all 6 required scenarios plus a complete integration workflow.

---

**Last Updated**: January 31, 2026
**Version**: 1.0
**Status**: Complete ✅
