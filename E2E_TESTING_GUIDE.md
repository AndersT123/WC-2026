# End-to-End Testing Guide

This guide shows how to perform end-to-end testing of the Witt-Classic prediction game without dealing with magic link authentication for multiple users.

## Overview

We provide two approaches:

1. **Automated Testing** - Run pytest E2E test suite
2. **Manual Testing** - Use seeded test data with API calls

## Approach 1: Automated E2E Testing (Recommended)

### Step 1: Seed Test Data

The seed script creates test users directly in the database, bypassing the magic link signup flow.

```bash
cd /home/anders/hello-scaleway
python3 scripts/seed_test_data.py
```

**Output:**
```
======================================================================
SEEDING TEST DATA
======================================================================

1. Creating test users...
   ✓ Created user: alice (alice@test.com)
   ✓ Created user: bob (bob@test.com)
   ✓ Created user: charlie (charlie@test.com)
   ✓ Created user: diana (diana@test.com)

2. Creating leagues...
   ✓ Created league: Test League 1 (Code: TEST0001)
   ✓ Created league: Test League 2 (Code: TEST0002)

...

TEST DATA CREATED SUCCESSFULLY
```

### Step 2: Start Backend

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Step 3: Run E2E Tests

```bash
pytest tests/test_e2e_scenarios.py -v
```

**Example Output:**
```
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_1_login_and_create_league PASSED
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_2_login_and_join_league PASSED
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_3_set_predictions_different_users PASSED
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_4_admin_update_results PASSED
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_5_witt_classic_scoring PASSED
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_6_league_standings_updated PASSED
tests/test_e2e_scenarios.py::TestE2EScenarios::test_complete_workflow PASSED
```

---

## Approach 2: Manual Testing with Seeded Data

### Step 1: Seed Test Data

```bash
python3 scripts/seed_test_data.py
```

This creates:
- 4 test users: alice, bob, charlie, diana
- 2 test leagues with different members
- Multiple matches (1 completed, 3 upcoming)
- Predictions for completed and upcoming matches

### Step 2: Get Login Tokens

After seeding, get the actual tokens from the database:

```bash
sqlite3 worldcup.db "SELECT email, token FROM magic_link_tokens WHERE email LIKE '%test.com%';"
```

**Output:**
```
alice@test.com|test_token_alice_a1b2c3d4
bob@test.com|test_token_bob_e5f6g7h8
charlie@test.com|test_token_charlie_i9j0k1l2
diana@test.com|test_token_diana_m3n4o5p6
```

### Step 3: Start Backend

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Step 4: Run Manual Tests

#### Test Scenario 1: Login and Create League

1. Open browser: `http://localhost:8080/login.html`
2. Enter: `alice@test.com`
3. Look for token in browser console or database
4. Click verify link to authenticate
5. Click "🏆 View Standings"
6. Verify you can see leagues

#### Test Scenario 2: Login and Join League

1. Log in as `bob@test.com`
2. Go to standings
3. Verify Bob is member of both leagues (one as creator, one as member)

#### Test Scenario 3: View Predictions

1. Log in as any user
2. Go to predictions page
3. Verify you can see your predictions for upcoming matches

#### Test Scenario 4: Admin Update Results

Use curl to update match results (requires admin access):

```bash
# Get match ID from database
MATCH_ID=$(sqlite3 worldcup.db "SELECT id FROM matches WHERE status='scheduled' LIMIT 1;")

# Update match result
curl -X PUT "http://localhost:8080/matches/$MATCH_ID/result" \
  -H "Content-Type: application/json" \
  -d '{
    "home_score": 2,
    "away_score": 1,
    "status": "completed"
  }' \
  -b "access_token=YOUR_TOKEN_HERE"
```

#### Test Scenario 5: Check Witt's-Classic Scoring

After updating a match result:

```bash
# Get updated predictions
sqlite3 worldcup.db "SELECT * FROM predictions WHERE match_id='$MATCH_ID';"
```

**Expected Output** (with points_earned calculated):
```
id|user_id|match_id|league_id|home_score|away_score|points_earned|...
a1|user_alice|match1|league1|2|1|5|...
b2|user_bob|match1|league1|2|0|3|...
c3|user_charlie|match1|league1|1|1|0|...
```

Points should follow Witt-Classic rules:
- Exact match: 5 points
- Correct winner + 1 score: 3 points
- Correct winner: 2 points
- One score: 1 point
- Nothing: 0 points

#### Test Scenario 6: Check League Standings

1. Log in as any user
2. Go to "🏆 View Standings"
3. Select a league
4. Verify leaderboard shows:
   - Correct rankings (based on total points)
   - Medals for top 3 (🥇🥈🥉)
   - All league members listed

---

## Test Data Summary

### Users Created
```
Username    | Email           | League 1  | League 2  | Role
------------|-----------------|-----------|-----------|----------
alice       | alice@test.com   | member    | member    |
bob         | bob@test.com     | member    | creator   |
charlie     | charlie@test.com | member    | -         |
diana       | diana@test.com   | -         | member    |
```

### Leagues Created
```
Name           | Code     | Creator | Members
---------------|----------|---------|---------------
Test League 1  | TEST0001 | alice   | alice, bob, charlie
Test League 2  | TEST0002 | bob     | bob, alice, diana
```

### Matches Created
```
#  | Home Team | Away Team | Status      | Result
---|-----------|-----------|-------------|------------
1  | Team A    | Team B    | completed   | 2-1
2  | Team C    | Team D    | scheduled   | -
3  | Team E    | Team F    | scheduled   | -
4  | Team G    | Team H    | scheduled   | -
```

### Predictions Created
- 3 predictions for completed match (with calculated points)
- 8 predictions for upcoming matches

---

## Testing All 6 Scenarios

### Scenario 1: Login and Create League ✓
- [x] User logs in
- [x] User creates new league
- [x] User is added as creator
- [x] Can view league in leaderboard

### Scenario 2: Login and Join League ✓
- [x] User logs in
- [x] User joins league with code
- [x] User appears in league members
- [x] User can view league standings

### Scenario 3: Set Predictions Different Users ✓
- [x] Multiple users make predictions
- [x] Predictions show in league
- [x] Each user sees their own predictions
- [x] Users can compare predictions

### Scenario 4: Admin Update Results ✓
- [x] Admin can update match scores
- [x] Admin can change match status
- [x] Match appears as completed
- [x] Non-admin cannot update results (403)

### Scenario 5: Witt's-Classic Scoring ✓
- [x] Exact score = 5 points
- [x] Correct winner + 1 score = 3 points
- [x] Correct winner only = 2 points
- [x] One score correct = 1 point
- [x] No matches = 0 points

### Scenario 6: League Standings Updated ✓
- [x] Standings show after match completes
- [x] Points calculated correctly
- [x] Leaderboard sorted by points
- [x] Rankings display correctly
- [x] Top 3 get medals

---

## Debugging

### Check Database State

```bash
# View all users
sqlite3 worldcup.db "SELECT id, username, email FROM users WHERE email LIKE '%test.com%';"

# View all leagues
sqlite3 worldcup.db "SELECT id, name, code FROM leagues WHERE code LIKE 'TEST%';"

# View matches
sqlite3 worldcup.db "SELECT id, home_team, away_team, status, home_score, away_score FROM matches LIMIT 5;"

# View predictions
sqlite3 worldcup.db "SELECT id, user_id, match_id, home_score, away_score, points_earned FROM predictions;"

# View memberships
sqlite3 worldcup.db "SELECT u.username, l.name, lm.role FROM league_memberships lm JOIN users u ON u.id=lm.user_id JOIN leagues l ON l.id=lm.league_id;"
```

### Reset Test Data

```bash
# Delete test data
rm worldcup.db

# Re-seed
python3 scripts/seed_test_data.py
```

### Check API Responses

```bash
# Get all leagues
curl -X GET "http://localhost:8080/leagues/" \
  -H "Cookie: access_token=YOUR_TOKEN"

# Get leaderboard for league
curl -X GET "http://localhost:8080/predictions/league/LEAGUE_ID/leaderboard" \
  -H "Cookie: access_token=YOUR_TOKEN"

# Get current user
curl -X GET "http://localhost:8080/auth/me" \
  -H "Cookie: access_token=YOUR_TOKEN"
```

---

## Automated Test Execution

### Run All E2E Tests

```bash
pytest tests/test_e2e_scenarios.py -v
```

### Run Specific Test

```bash
pytest tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_1_login_and_create_league -v
```

### Run Complete Workflow Test Only

```bash
pytest tests/test_e2e_scenarios.py::TestE2EScenarios::test_complete_workflow -v
```

### Run with Detailed Output

```bash
pytest tests/test_e2e_scenarios.py -v -s
```

---

## Common Issues & Solutions

### Issue: "Database locked"
**Solution**: Close any open database connections
```bash
# Ensure no other processes have the database open
lsof worldcup.db
```

### Issue: "Tests fail with authentication errors"
**Solution**: Verify backend is running
```bash
curl http://localhost:8080/health
```

### Issue: "Predictions not appearing in leaderboard"
**Solution**: Ensure predictions are for completed matches with calculated points
```bash
# Check if points_earned is NULL
sqlite3 worldcup.db "SELECT * FROM predictions WHERE points_earned IS NULL;"
```

### Issue: "Admin endpoint returns 403"
**Solution**: Verify user email is in ADMIN_EMAILS config
```bash
grep ADMIN_EMAILS .env
```

---

## Test Coverage

The E2E test suite covers:

| Scenario | Test | Coverage |
|----------|------|----------|
| 1 | test_scenario_1_login_and_create_league | League creation, membership |
| 2 | test_scenario_2_login_and_join_league | League joining, multiple members |
| 3 | test_scenario_3_set_predictions_different_users | Predictions, multiple users |
| 4 | test_scenario_4_admin_update_results | Admin endpoint, match update |
| 5 | test_scenario_5_witt_classic_scoring | All 5 scoring rules |
| 6 | test_scenario_6_league_standings_updated | Point calculation, leaderboard |
| Bonus | test_complete_workflow | Full end-to-end flow |

---

## Files

- **Test Data Seeder**: `scripts/seed_test_data.py`
- **E2E Test Suite**: `tests/test_e2e_scenarios.py`
- **This Guide**: `E2E_TESTING_GUIDE.md`

---

## Next Steps

1. ✅ Run `seed_test_data.py` to create test data
2. ✅ Start backend server
3. ✅ Run `pytest tests/test_e2e_scenarios.py -v`
4. ✅ All tests should pass
5. ✅ Manually verify UI works with test users

**Happy testing!** 🚀
