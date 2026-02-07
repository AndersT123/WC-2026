# Testing Guide: Predictions & Scores Persistence

This guide explains how to test data persistence, prediction saving, score calculation, and admin result input across different test sessions and scenarios.

## Understanding Test Database Isolation

### Current Setup

```
Each test run:
1. Fresh database is created
2. Test executes
3. Database is cleaned up
↓
RESULT: Clean slate for next test (good for isolation, bad for session testing)
```

**Why this is good:**
- Tests don't interfere with each other
- Reproducible results
- Can run tests in any order

**Why this is bad for session testing:**
- Can't test persistence across restarts manually
- Need to write tests to verify persistence instead

## Option 1: Test Persistence Within a Test Session (Recommended)

We've created **`tests/test_predictions_persistence.py`** which demonstrates persistence across "sessions" within a single test.

### What These Tests Verify

```
✓ test_prediction_saved_to_database_and_persists
  - User makes prediction
  - Prediction is saved to database
  - Prediction persists in a simulated new request (Session 2)
  - Data is retrieved correctly

✓ test_admin_inputs_result_and_predictions_scored
  - User makes prediction (Session 1)
  - Admin inputs match result (Session 2)
  - Points are calculated (Session 3)
  - Points persist and can be retrieved (Session 4)

✓ test_multiple_users_predictions_and_leaderboard
  - Multiple users make different predictions
  - Admin inputs result
  - System calculates different scores for each user
  - Leaderboard is built from persisted data

✓ test_multiple_matches_and_cumulative_scores
  - User makes predictions for 3 matches
  - Admin inputs results for all matches
  - Points accumulate correctly across matches
  - Total score is verified
```

### Run the Persistence Tests

```bash
# Run all persistence tests
python3 -m pytest tests/test_predictions_persistence.py -v -s

# Run a specific test with detailed output
python3 -m pytest tests/test_predictions_persistence.py::TestPredictionPersistence::test_admin_inputs_result_and_predictions_scored -v -s

# Run with timing info
python3 -m pytest tests/test_predictions_persistence.py -v --durations=0
```

Output shows each "session" step:
```
✓ Session 1: Prediction saved to database
✓ Session 2: Prediction persisted and retrieved from database
✓ Session 1: Prediction created before match result
✓ Session 2: Admin inputted match result (2-1)
✓ Session 3: Points calculated and saved (5 points for exact match)
✓ Session 4: Points persisted in database (5 points)
```

## Option 2: Manual Testing with Persistent Local Database

For manual/integration testing, use a persistent SQLite database instead of the test database.

### Setup Persistent Local Database

1. **Create a development database** (not the test database):

```bash
# Edit your .env file to use a persistent database
# Change from: DATABASE_URL=sqlite+aiosqlite:///./test.db
# To: DATABASE_URL=sqlite+aiosqlite:///./dev.db
```

2. **Run migrations** (if using Alembic):

```bash
# Create tables
alembic upgrade head
```

Or just start the app - tables will be created automatically.

3. **Start the development server**:

```bash
# In one terminal
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Make requests** in another terminal (or use your frontend):

```bash
# Create a league
curl -X POST http://localhost:8000/leagues \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=YOUR_TOKEN" \
  -d '{"name": "Test League"}'

# Join a league
curl -X POST http://localhost:8000/leagues/join \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=YOUR_TOKEN" \
  -d '{"code": "ABC12345"}'
```

**Key Point:** With persistent database, data survives:
- Server restarts
- Test runs
- Multiple requests across sessions

### Database File Location

```
/home/anders/hello-scaleway/dev.db  ← Your persistent local database
/home/anders/hello-scaleway/test.db ← Used by tests (fresh each time)
```

## Option 3: Write Custom Multi-Session Tests

If you need to test specific workflows, create tests in `test_predictions_persistence.py` following this pattern:

```python
@pytest.mark.asyncio
async def test_my_custom_workflow(self, client, db):
    """Test a specific workflow across simulated sessions."""

    # **Session 1: Setup**
    user = User(...)
    db.add(user)
    await db.flush()
    await db.commit()

    # **Session 2: User action**
    prediction = Prediction(...)
    db.add(prediction)
    await db.flush()
    await db.commit()

    # **Session 3: Verify persistence**
    result = await db.execute(select(Prediction).where(...))
    persisted = result.scalar_one()
    assert persisted.points_earned == expected_value
```

## Data Persistence Verification Checklist

When testing predictions & scores, verify:

- [ ] **Prediction Saved**: Prediction row exists in database after `commit()`
- [ ] **Prediction Retrieves**: Can fetch prediction by `SELECT` after commit
- [ ] **Score Calculated**: `points_earned` field is set after admin inputs result
- [ ] **Score Persisted**: Points value survives database query
- [ ] **Multiple Users**: Each user gets correct points (not shared)
- [ ] **Cumulative Scores**: Points add up across multiple predictions
- [ ] **Leaderboard**: Can build leaderboard by `SELECT` and `SUM(points)`

## Example: Complete Workflow Test

Here's how to test the complete flow:

```python
# 1. User creates league
league = League(...)
# 2. User makes prediction
prediction = Prediction(home_score=2, away_score=1)
# 3. Admin inputs result
match.home_score = 2
match.away_score = 1
# 4. Calculate points
if prediction.home_score == match.home_score and prediction.away_score == match.away_score:
    prediction.points_earned = 5
# 5. Verify persistence
fetched = db.execute(select(Prediction).where(...)).scalar_one()
assert fetched.points_earned == 5
```

This entire flow is in `test_admin_inputs_result_and_predictions_scored()`.

## Running All Tests

```bash
# Run league tests
python3 -m pytest tests/test_league_endpoints.py -v

# Run prediction persistence tests
python3 -m pytest tests/test_predictions_persistence.py -v

# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=html
```

## Key Insights

1. **Test isolation is good** - Each test gets a fresh database
2. **Multi-session within a test** - You can simulate multiple sessions in one test by:
   - Create data
   - Flush to database
   - Query/modify data
   - Flush again
   - Verify persistence
3. **Persistent database is for manual testing** - Use `dev.db` for exploring the API
4. **Tests are for automated verification** - Write tests for workflows you want to guarantee work

## Summary

| Scenario | Tool | Method |
|----------|------|--------|
| Test data persists across requests | Unit/Integration Test | `test_predictions_persistence.py` |
| Manually test API & see data persist | Dev Server | Use `dev.db` database |
| Verify complete workflows | Custom Tests | Add to `test_predictions_persistence.py` |
| Run before committing | CI/Automation | `pytest tests/` |

All data in tests is persisted correctly - the database is just recreated for each test run! 🎉
