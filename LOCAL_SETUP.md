# Local Setup Instructions - Complete Guide

**Time Required**: 5-10 minutes
**Prerequisites**: Python 3.8+, pip

---

## ⚡ Quick Login (After Setup Complete)

Once the backend is running, use these links to login:

```
Alice:   http://localhost:8080/auth/verify?token=test_token_alice_fixed123
Bob:     http://localhost:8080/auth/verify?token=test_token_bob_fixed456
Charlie: http://localhost:8080/auth/verify?token=test_token_charlie_fixed789
Diana:   http://localhost:8080/auth/verify?token=test_token_diana_fixed000
```

**After login**: You'll auto-redirect to the predictions page
**Click "🏆 Standings"**: View the league leaderboard

---

## Step 1: Navigate to Project Directory

```bash
cd /home/anders/hello-scaleway
```

Verify you're in the right place:
```bash
ls -la | grep -E "app|requirements|league-standings"
```

You should see:
- `app/` directory
- `requirements.txt`
- `league-standings.html`

---

## Step 2: Install Dependencies (First Time Only)

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI (backend framework)
- SQLAlchemy (database)
- Uvicorn (web server)
- pytest (testing)
- And other dependencies

**Expected output**: Should show "Successfully installed..." for multiple packages

---

## Step 3: Create Test Database with Data

```bash
python3 scripts/seed_test_data.py
```

**What this does:**
- Creates `worldcup.db` database file
- Adds 4 test users (alice, bob, charlie, diana)
- Adds 2 test leagues (Test League 1, Test League 2)
- Adds 4 matches (1 completed, 3 upcoming)
- Calculates points for predictions

**Expected output:**
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

3. Adding users to leagues...
   ✓ Added alice to Test League 1 as creator
   ✓ Added bob to Test League 1 as member
   ... (more output)

TEST DATA CREATED SUCCESSFULLY
======================================================================
```

**Verify database was created:**
```bash
ls -lh worldcup.db
```

Should show a file like: `-rw-r--r-- 1 anders anders 32K Jan 31 22:12 worldcup.db`

---

## Step 4: Start the Backend Server

Open a **new terminal** (keep the first one for running commands later):

```bash
cd /home/anders/hello-scaleway
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete
```

**Verify backend is running:**

Open another terminal and run:
```bash
curl http://localhost:8080/health
```

Should return:
```
{"status":"healthy"}
```

---

## Step 5: Open in Browser and Test

### 5.1 View League Standings Page

Open your browser and go to:
```
http://localhost:8080/league-standings.html
```

**You should see:**
- League selector with "Test League 1" and "Test League 2" cards
- Click on a league to see the leaderboard
- Players listed with their points:
  - alice: 5 points 🥇 (gold medal)
  - bob: 3 points 🥈 (silver medal)
  - charlie: 1 point 🥉 (bronze medal)

### 5.2 View Login Page

Open your browser and go to:
```
http://localhost:8080/login.html
```

**You should see:**
- Email input field
- "🏆 View Standings" button in the authenticated view
- Click the button to go to standings

### 5.3 View Predictions Page

Open your browser and go to:
```
http://localhost:8080/witt-classic.html
```

**You should see:**
- Match listings (Team A vs Team B, Team C vs Team D, etc.)
- Prediction form
- "🏆 Standings" button in header

---

## Step 6: Run Tests (Optional but Recommended)

Open a terminal and run:

```bash
cd /home/anders/hello-scaleway
pytest tests/test_e2e_scenarios.py -v
```

**Expected output:**
```
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_1_login_and_create_league PASSED [ 14%]
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_2_login_and_join_league PASSED [ 28%]
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_3_set_predictions_different_users PASSED [ 42%]
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_4_admin_update_results PASSED [ 57%]
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_5_witt_classic_scoring PASSED [ 71%]
tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_6_league_standings_updated PASSED [ 85%]
tests/test_e2e_scenarios.py::TestE2EScenarios::test_complete_workflow PASSED [100%]

============================== 7 passed in 2.48s ===============================
```

**All 7 tests should PASS** ✅

---

## Complete Setup Summary

| Step | Command | Result |
|------|---------|--------|
| 1 | `cd /home/anders/hello-scaleway` | Navigate to project |
| 2 | `pip install -r requirements.txt` | Install dependencies |
| 3 | `python3 scripts/seed_test_data.py` | Create database with test data |
| 4 | `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080` | Start backend |
| 5 | Visit `http://localhost:8080/league-standings.html` | View in browser |
| 6 | `pytest tests/test_e2e_scenarios.py -v` | Run all tests |

---

## 🎯 What You Should See

### League Standings Page
```
┌─────────────────────────────────┐
│   League Standings              │
│                                 │
│  [Test League 1]  [Test League 2] │
│                                 │
│  LEADERBOARD                    │
│  ─────────────────────────────  │
│  🥇 alice        5 pts          │
│  🥈 bob          3 pts          │
│  🥉 charlie      1 pt           │
│                                 │
└─────────────────────────────────┘
```

### Test Results
```
7 passed in 2.48s ✅
```

### Backend Running
```
Uvicorn running on http://0.0.0.0:8080 ✅
```

---

## 🧪 Test Data Overview & Login Links

**Users with Fixed Login Tokens** (Same every time):

### Alice
- Email: alice@test.com
- Token: `test_token_alice_fixed123`
- Login: http://localhost:8080/auth/verify?token=test_token_alice_fixed123
- Role: Creator of League 1, Member of League 2

### Bob
- Email: bob@test.com
- Token: `test_token_bob_fixed456`
- Login: http://localhost:8080/auth/verify?token=test_token_bob_fixed456
- Role: Member of League 1, Creator of League 2

### Charlie
- Email: charlie@test.com
- Token: `test_token_charlie_fixed789`
- Login: http://localhost:8080/auth/verify?token=test_token_charlie_fixed789
- Role: Member of League 1

### Diana
- Email: diana@test.com
- Token: `test_token_diana_fixed000`
- Login: http://localhost:8080/auth/verify?token=test_token_diana_fixed000
- Role: Member of League 2

**Leagues:**
- Test League 1 (TEST0001) - Members: alice, bob, charlie
- Test League 2 (TEST0002) - Members: bob, alice, diana

**Matches:**
- Team A vs Team B (COMPLETED 2-1)
  - alice predicted 2-1 → 5 points ✅
  - bob predicted 2-0 → 3 points ✅
  - charlie predicted 1-1 → 1 point ✅
- Team C vs Team D (SCHEDULED)
- Team E vs Team F (SCHEDULED)
- Team G vs Team H (SCHEDULED)

---

## 🛑 How to Stop Everything

**To stop the backend:**
- Press `Ctrl+C` in the terminal where the backend is running

**To clear and restart:**
```bash
# Remove database
rm worldcup.db

# Re-seed with fresh data
python3 scripts/seed_test_data.py

# Restart backend (it will recreate database)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 📞 Common Issues & Solutions

### Issue: Port 8080 Already In Use
```bash
# Kill the existing process
pkill -f "uvicorn app.main"

# Or use a different port
python3 -m uvicorn app.main:app --port 8081
# Then visit http://localhost:8081/league-standings.html
```

### Issue: "ModuleNotFoundError: No module named 'app'"
```bash
# Make sure you're in the right directory
cd /home/anders/hello-scaleway

# And have dependencies installed
pip install -r requirements.txt
```

### Issue: Database File Not Found
```bash
# Recreate the database
python3 scripts/seed_test_data.py
```

### Issue: Tests Show Import Errors
```bash
# Make sure conftest.py exists
ls tests/conftest.py

# Run pytest from project root
cd /home/anders/hello-scaleway
pytest tests/test_e2e_scenarios.py -v
```

### Issue: Browser Shows "Connection Refused"
```bash
# Verify backend is running
curl http://localhost:8080/health

# If it fails, check if something else is using port 8080
# Start backend in new terminal
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 🔍 Verification Checklist

Use this to verify everything works:

```bash
# 1. Check dependencies installed
pip list | grep -E "fastapi|sqlalchemy|uvicorn|pytest"

# 2. Check database exists
ls -lh worldcup.db

# 3. Check backend health
curl http://localhost:8080/health
# Should return: {"status":"healthy"}

# 4. Check test data
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM users WHERE email LIKE '%test.com%'")
users = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM leagues WHERE code LIKE 'TEST%'")
leagues = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM matches")
matches = cursor.fetchone()[0]
print(f"Users: {users}, Leagues: {leagues}, Matches: {matches}")
conn.close()
EOF
# Should return: Users: 4, Leagues: 2, Matches: 4

# 5. Run tests
pytest tests/test_e2e_scenarios.py -v
# Should show: 7 passed
```

---

## 📋 Terminal Setup (Recommended)

For best experience, use 2-3 terminals:

**Terminal 1 - Backend:**
```bash
cd /home/anders/hello-scaleway
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
# Leave this running - you'll see logs here
```

**Terminal 2 - Commands:**
```bash
cd /home/anders/hello-scaleway
# Use this for running tests, commands, etc.

# Example: Run tests
pytest tests/test_e2e_scenarios.py -v

# Example: Check database
sqlite3 worldcup.db ".tables"

# Example: Seed data
python3 scripts/seed_test_data.py
```

**Browser - View Interface:**
- http://localhost:8080/league-standings.html
- http://localhost:8080/login.html
- http://localhost:8080/witt-classic.html

---

## 🚀 Next Steps After Setup

1. **Explore the standings page** - See how the leaderboard looks
2. **Try the login page** - Verify authentication works
3. **Run the tests** - Confirm all 7 scenarios pass
4. **Read the documentation** - Check `QUICK_START.md` or `PROJECT_STATUS.md`
5. **Test the API** - Use curl commands to update matches

---

## 📚 Quick Command Reference

```bash
# Setup
cd /home/anders/hello-scaleway
pip install -r requirements.txt
python3 scripts/seed_test_data.py

# Run backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Run tests
pytest tests/test_e2e_scenarios.py -v

# View database
sqlite3 worldcup.db "SELECT username, email FROM users WHERE email LIKE '%test.com%'"

# Kill backend
pkill -f "uvicorn app.main"

# Reset everything
rm worldcup.db
python3 scripts/seed_test_data.py
```

---

## ✅ Success Indicators

You'll know everything is working when you see:

✅ Backend running on http://0.0.0.0:8080
✅ Browser shows league standings with alice (5 pts), bob (3 pts), charlie (1 pt)
✅ All 7 tests pass in ~2.5 seconds
✅ Database has 4 users, 2 leagues, 4 matches

---

**You're all set! Start with Step 1 above and follow each step in order.** 🚀

