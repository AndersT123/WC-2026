# Session-Based Testing with Persistent Database

You now have **two testing modes** that coexist peacefully! Keep using unit tests for CI/CD, and use session-based testing for local development and multi-step workflow testing.

## Quick Start

### Mode 1: Unit Testing (Default) ✓
```bash
# Fresh database for each test (isolation)
python3 -m pytest tests/test_league_endpoints.py -v

# All tests pass: 22 passed ✓
```

**Use when:**
- Running automated tests in CI/CD
- Testing isolated features
- Want reproducible test results

---

### Mode 2: Session Testing (New!) ✓
```bash
# Persistent database - data survives across test runs!
PYTEST_MODE=session python3 -m pytest tests/test_predictions_persistence.py -v

# Database file: /home/anders/hello-scaleway/session.db
# Data persists between runs!
```

**Use when:**
- Testing realistic multi-step workflows
- Building up complex data scenarios
- Testing prediction scoring with real data
- Debugging features with accumulated state

---

## Managing Session Database

### View Database Status
```bash
python3 manage_session_db.py status
# Shows: database file, size, table count

python3 manage_session_db.py tables
# Shows: User (6 rows), League (4 rows), Match (6 rows), Prediction (8 rows)
```

### Reset Persistent Database
```bash
# Delete all data and start fresh
python3 manage_session_db.py reset
# Prompts: "Delete all data? (yes/no):"

# Clear specific table
python3 manage_session_db.py clear predictions
python3 manage_session_db.py clear users
```

---

## How It Works

### Unit Testing (conftest.py - Default)
```python
# Each test:
1. Create fresh in-memory database
2. Run test
3. Rollback changes
4. Delete tables
↓
Next test gets clean slate
```

### Session Testing (conftest.py with PYTEST_MODE=session)
```python
# Each test run:
1. Connect to session.db file
2. Create tables if they don't exist
3. Run test
4. COMMIT changes (data persists!)
5. Keep database file
↓
Next test run has accumulated data
```

---

## Practical Examples

### Example 1: Test Multi-Step Prediction Workflow

```bash
# Run persistence tests - creates data in session.db
PYTEST_MODE=session python3 -m pytest tests/test_predictions_persistence.py::TestPredictionPersistence::test_admin_inputs_result_and_predictions_scored -v

# Check what was created
python3 manage_session_db.py tables
# User (1), League (1), Match (1), Prediction (1)

# Run another test - uses existing data
PYTEST_MODE=session python3 -m pytest tests/test_predictions_persistence.py::TestPredictionPersistence::test_multiple_users_predictions_and_leaderboard -v

# Check accumulated data
python3 manage_session_db.py tables
# User (3), League (1), LeagueMembership (3), Match (1), Prediction (2)
```

### Example 2: Start Fresh for New Feature

```bash
# Reset everything
python3 manage_session_db.py reset

# Run tests against fresh database
PYTEST_MODE=session python3 -m pytest tests/test_predictions_persistence.py -v
```

### Example 3: Debug with Persistent State

```bash
# Run tests that populate data
PYTEST_MODE=session pytest tests/test_predictions_persistence.py -v

# Check the data
python3 manage_session_db.py tables

# Now write a quick debug script that queries this data:
# (session.db contains real test data you can inspect)
```

---

## Test Coverage

### Unit Tests (22 passing)
- League creation, joining, listing
- Member counts and leaderboards
- Error handling (401, 404, 409, 422)
- Multi-user scenarios

**Run:** `pytest tests/test_league_endpoints.py`

### Session Tests (4 passing)
- Prediction persistence
- Admin result input and scoring
- Multi-user predictions & leaderboards
- Cumulative scores across matches

**Run:** `PYTEST_MODE=session pytest tests/test_predictions_persistence.py`

---

## Configuration Files

| File | Purpose |
|------|---------|
| `tests/conftest.py` | Main test configuration (supports both modes) |
| `pytest.ini` | Unit test config (default) |
| `pytest_session.ini` | Session test config (can be used with `-c` flag) |
| `manage_session_db.py` | Database management script |
| `session.db` | Persistent session database (created automatically) |

---

## Environment Variable

Set `PYTEST_MODE=session` to enable session-based testing:

```bash
# Unit mode (default)
pytest tests/

# Session mode
PYTEST_MODE=session pytest tests/

# Also works with pytest_session.ini config
PYTEST_MODE=session pytest -c pytest_session.ini tests/
```

---

## Complete Example Workflow

```bash
# 1. Run unit tests (fresh database each time)
pytest tests/test_league_endpoints.py -v
# ✓ 22 passed

# 2. Run session tests to populate session.db
PYTEST_MODE=session pytest tests/test_predictions_persistence.py -v
# ✓ 4 passed

# 3. Check accumulated data in session.db
python3 manage_session_db.py tables
# User (6), League (4), Match (6), Prediction (8)

# 4. Reset if needed
python3 manage_session_db.py reset

# 5. Run again to verify reset worked
python3 manage_session_db.py status
```

---

## Key Differences

| Aspect | Unit Testing | Session Testing |
|--------|---|---|
| Database | Fresh for each test | Persistent (session.db) |
| Data Cleanup | Automatic (rollback) | Manual (reset command) |
| Use Case | Isolated testing | Workflow testing |
| Survives Restart | ❌ No | ✅ Yes |
| Good for CI/CD | ✅ Yes | ❌ No |
| Good for Dev | ❌ No | ✅ Yes |
| Database File | None (in-memory) | `session.db` |

---

## Benefits

### Unit Testing Benefits ✓
- Fast (in-memory database)
- Isolated (no cross-test interference)
- Reproducible (fresh start each time)
- Safe for CI/CD

### Session Testing Benefits ✓
- Realistic (data persists)
- Debuggable (can inspect accumulated state)
- Efficient (reuse data across tests)
- Great for development

---

## Database Management Commands

```bash
# View status
python3 manage_session_db.py status

# List tables with counts
python3 manage_session_db.py tables

# Reset all data
python3 manage_session_db.py reset

# Clear specific table
python3 manage_session_db.py clear users
python3 manage_session_db.py clear predictions
python3 manage_session_db.py clear matches
python3 manage_session_db.py clear leagues
python3 manage_session_db.py clear league_memberships
```

---

## Troubleshooting

### Tests still use old data

```bash
# Reset the persistent database
python3 manage_session_db.py reset

# Then run tests again
PYTEST_MODE=session pytest tests/
```

### "Database is locked" error

```bash
# Kill any running pytest/server processes
# Reset the database
python3 manage_session_db.py reset

# Try again
PYTEST_MODE=session pytest tests/
```

### Need to inspect session database

The `session.db` file is a standard SQLite database. You can inspect it with:

```bash
sqlite3 session.db

# Inside sqlite3:
sqlite> .tables
sqlite> SELECT COUNT(*) FROM users;
sqlite> SELECT COUNT(*) FROM predictions;
sqlite> .quit
```

---

## Summary

You now have the perfect testing setup:

- **Unit Tests** (default): Fast, isolated, reproducible → Great for CI/CD
- **Session Tests** (PYTEST_MODE=session): Persistent, realistic, debuggable → Great for development

Both modes coexist peacefully! 🎉

Use unit tests for automated testing pipelines, and session tests for local development and complex workflow testing.
