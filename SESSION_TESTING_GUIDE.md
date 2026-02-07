# Session-Based Testing Guide

This guide explains how to use persistent session-based testing where data survives across test runs, server restarts, and multiple sessions.

## Overview

You now have **two testing modes**:

### Unit Testing (Default) ✓
```
- Fresh database for each test
- Tests isolated and reproducible
- Run: pytest tests/
- Database: Fresh each time (automatic cleanup)
```

### Session-Based Testing (New) ✓
```
- Persistent database in project folder
- Data survives test runs and server restarts
- Run: pytest -c pytest_session.ini tests/
- Database: session.db (in project root)
```

## Quick Start: Session-Based Testing

### 1. Run Tests with Persistent Database

```bash
# First time - creates session.db with fresh tables
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py -v -s

# Subsequent runs - data persists from previous run
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py -v -s
```

### 2. Check Database Status

```bash
# View database info and row counts
python3 manage_session_db.py status
python3 manage_session_db.py tables
```

Output:
```
📊 Session Database Status
============================================================
Database File: /home/anders/hello-scaleway/session.db
Path Exists: True
Size: 0.05 MB
Tables: 5
  - users, leagues, league_memberships, matches, predictions
============================================================

📋 Database Tables and Row Counts
============================================================
  User                      3 rows
  League                    2 rows
  LeagueMembership          4 rows
  Match                     1 rows
  Prediction                5 rows
============================================================
```

### 3. Reset Data When Needed

```bash
# Reset entire database (removes all data)
python3 manage_session_db.py reset

# Clear specific table
python3 manage_session_db.py clear predictions
python3 manage_session_db.py clear users
```

## File Locations

```
/home/anders/hello-scaleway/
├── session.db                    ← Persistent session database (created by pytest)
├── conftest.py                   ← Unit test configuration (fresh DB)
├── tests/
│   ├── conftest_session.py       ← Session test configuration (persistent DB)
│   └── test_predictions_persistence.py
├── pytest.ini                    ← Default unit test config
├── pytest_session.ini            ← Session test config
└── manage_session_db.py          ← Database management script
```

## Workflow Examples

### Example 1: Test Multi-Session Predictions

```bash
# First test run - creates data
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py::TestPredictionPersistence::test_admin_inputs_result_and_predictions_scored -v

# Data persisted in session.db:
# - 1 user
# - 1 league
# - 1 match with result (2-1)
# - 1 prediction with points (5)

# Second test run - data still there
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py::TestPredictionPersistence::test_multiple_users_predictions_and_leaderboard -v

# Check what was created
python3 manage_session_db.py tables
```

### Example 2: Build Up Data Across Sessions

```bash
# Session 1: Create base setup
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py::TestPredictionPersistence::test_prediction_saved_to_database_and_persists -v

python3 manage_session_db.py tables
# Shows: 1 user, 1 league, 1 match, 1 prediction

# Session 2: Add more predictions
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py::TestPredictionPersistence::test_multiple_users_predictions_and_leaderboard -v

python3 manage_session_db.py tables
# Shows: 3 users, 1 league, 3 league_memberships, 1 match, 4 predictions

# Session 3: Test leaderboard with all accumulated data
# (Write a custom test that queries the existing data)
```

### Example 3: Fresh Start for New Feature Testing

```bash
# Reset everything
python3 manage_session_db.py reset

# Start fresh testing
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py -v
```

## Writing Session-Based Tests

Session-based tests use the same patterns as unit tests, but data persists:

```python
@pytest.mark.asyncio
async def test_my_session_workflow(self, client, db):
    """This test uses persistent session database."""

    # Data you create here survives after test finishes
    user = User(id=uuid.uuid4(), username="persistent_user", ...)
    db.add(user)
    await db.flush()
    await db.commit()  # Data persists!

    # Subsequent tests can query this data:
    result = await db.execute(select(User).where(User.username == "persistent_user"))
    same_user = result.scalar_one()
    assert same_user.username == "persistent_user"
```

**Key difference from unit tests:** Data is committed and NOT rolled back.

## Running Tests

### Unit Tests (Fresh Database Each Time)
```bash
# Default mode - uses conftest.py
python3 -m pytest tests/ -v

# Only league tests
python3 -m pytest tests/test_league_endpoints.py -v

# Only specific test
python3 -m pytest tests/test_league_endpoints.py::TestLeagueCreation::test_create_league_success -v
```

### Session Tests (Persistent Database)
```bash
# All session tests
python3 -m pytest -c pytest_session.ini tests/ -v

# Only predictions persistence
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py -v

# Specific test with output
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py::TestPredictionPersistence::test_admin_inputs_result_and_predictions_scored -v -s
```

## Manual Testing with Session Database

You can also use the persistent session database for manual API testing:

```bash
# Terminal 1: Start development server
python3 -m uvicorn app.main:app --reload

# Terminal 2: Run session tests to populate data
python3 -m pytest -c pytest_session.ini tests/test_predictions_persistence.py -v

# Terminal 3: Query the populated data
python3 manage_session_db.py tables

# Make manual API requests with curl or Postman
curl http://localhost:8000/leagues -H "Cookie: access_token=YOUR_TOKEN"
```

## Database Management Commands

### View Status
```bash
python3 manage_session_db.py status

# Output:
# 📊 Session Database Status
# ============================================================
# Database File: /home/anders/hello-scaleway/session.db
# Path Exists: True
# Size: 0.15 MB
# Tables: 5
#   - users, leagues, league_memberships, matches, predictions
# ============================================================
```

### List Tables and Counts
```bash
python3 manage_session_db.py tables

# Output:
# 📋 Database Tables and Row Counts
# ============================================================
#   User                      5 rows
#   League                    2 rows
#   LeagueMembership          7 rows
#   Match                     3 rows
#   Prediction               12 rows
# ============================================================
```

### Reset Entire Database
```bash
python3 manage_session_db.py reset

# Prompts: "Delete all data? (yes/no):"
# Then recreates empty tables
```

### Clear Specific Table
```bash
# Clear only predictions (keep users, leagues, matches)
python3 manage_session_db.py clear predictions

# Clear only matches
python3 manage_session_db.py clear matches
```

## Use Cases

### Use Unit Testing When:
- Running automated tests in CI/CD
- Writing tests that should be isolated
- Testing edge cases and error scenarios
- You want reproducible test results

### Use Session Testing When:
- Testing realistic multi-step workflows
- Building up complex data scenarios
- Testing leaderboard calculations with real data
- Debugging prediction scoring logic
- Testing admin features with pre-populated data
- Verifying data persists across sessions

## Troubleshooting

### Tests Still Using Old Database

**Problem:** Tests show old data even after restart

**Solution:** Explicitly reset
```bash
python3 manage_session_db.py reset
```

### Can't See New Data

**Problem:** Inserted data doesn't show up

**Solution:** Make sure to commit:
```python
db.add(my_object)
await db.flush()
await db.commit()  # Must commit for session tests!
```

### Database Locked Error

**Problem:** "database is locked"

**Solution:** Close other connections to session.db and retry
```bash
# Kill any running tests/servers
# Reset the database
python3 manage_session_db.py reset
# Try again
python3 -m pytest -c pytest_session.ini tests/ -v
```

## Architecture

### Unit Testing Flow
```
conftest.py
  ↓
Creates fresh SQLite database
  ↓
Runs test
  ↓
Rolls back all changes
  ↓
Clean up (drop all tables)
  ↓
Ready for next test
```

### Session Testing Flow
```
conftest_session.py
  ↓
Connects to session.db (creates if missing)
  ↓
Runs test
  ↓
COMMITS changes (data persists!)
  ↓
Keeps database file
  ↓
Ready for next test run with accumulated data
```

## Summary

| Feature | Unit Tests | Session Tests |
|---------|-----------|--------------|
| Database | Fresh each time | Persistent (session.db) |
| Data Cleanup | Automatic (rollback) | Manual (reset command) |
| Use Case | Isolated testing | Workflow testing |
| Config | pytest.ini (default) | pytest_session.ini |
| Command | `pytest tests/` | `pytest -c pytest_session.ini tests/` |
| Data Survives | No | Yes ✓ |
| Server Restart | No | Yes ✓ |
| Good for CI/CD | Yes ✓ | No |
| Good for Development | No | Yes ✓ |

Both modes coexist peacefully! Use the right tool for the job. 🎯
