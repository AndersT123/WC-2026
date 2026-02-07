# Quick Start Guide

## TL;DR - Start Here

### 1. Run E2E Tests (30 seconds)
```bash
bash run_e2e_tests.sh
```

### 2. View League Standings
```bash
# Start backend first
python3 -m uvicorn app.main:app --port 8080

# Then visit
http://localhost:8080/league-standings.html
```

### 3. Update Match Results (Admin)
```bash
curl -X PUT http://localhost:8080/matches/{match_id}/result \
  -H "Content-Type: application/json" \
  -d '{"home_score": 2, "away_score": 1, "status": "completed"}'
```

---

## What's New

| Feature | Description | File |
|---------|-------------|------|
| Admin Endpoint | Update matches & auto-calculate scores | `app/routers/matches.py` |
| Standings Page | View league leaderboards | `league-standings.html` |
| E2E Tests | Automated test suite (7 scenarios) | `tests/test_e2e_scenarios.py` |

---

## Quick Commands

### Setup
```bash
# Seed test data (creates 4 users, 2 leagues, 4 matches)
python3 scripts/seed_test_data.py

# Verify database
python3 scripts/verify_database.py  # (if exists)
```

### Testing
```bash
# Run all tests
pytest tests/test_e2e_scenarios.py -v

# Run specific test
pytest tests/test_e2e_scenarios.py::TestE2EScenarios::test_scenario_1_login_and_create_league -v

# Run with output
pytest tests/test_e2e_scenarios.py -v -s
```

### Backend
```bash
# Start backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Health check
curl http://localhost:8080/health
```

### Database
```bash
# View test users
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()
cursor.execute("SELECT username, email FROM users WHERE email LIKE '%test.com%'")
for row in cursor.fetchall():
    print(f"{row[0]:15} | {row[1]}")
conn.close()
EOF

# View leagues
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()
cursor.execute("SELECT name, code FROM leagues WHERE code LIKE 'TEST%'")
for row in cursor.fetchall():
    print(f"{row[0]:20} | {row[1]}")
conn.close()
EOF

# View matches
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()
cursor.execute("SELECT home_team, away_team, status FROM matches")
for row in cursor.fetchall():
    print(f"{row[0]:10} vs {row[1]:10} | {row[2]}")
conn.close()
EOF
```

---

## Test Scenarios

All covered by E2E tests:

1. ✅ Login and create league
2. ✅ Login and join league
3. ✅ Set predictions (multiple users)
4. ✅ Admin update match results
5. ✅ Witt-Classic scoring validation
6. ✅ League standings calculation
7. ✅ Complete end-to-end workflow

**Run all**: `pytest tests/test_e2e_scenarios.py -v`

---

## API Endpoints

### Auth
- `GET /auth/me` - Current user info

### Leagues
- `GET /leagues/` - User's leagues
- `POST /leagues/` - Create league
- `POST /leagues/join` - Join league

### Matches (Admin)
- `GET /matches/` - All matches
- `PUT /matches/{id}/result` - Update result (admin only)

### Predictions
- `POST /predictions/` - Create prediction
- `GET /predictions/league/{id}/leaderboard` - Get standings

---

## Test Data

**Users**: alice, bob, charlie, diana (all @test.com)

**Leagues**:
- Test League 1 (TEST0001) - alice (creator), bob, charlie
- Test League 2 (TEST0002) - bob (creator), alice, diana

**Matches**:
- Team A vs Team B (completed, 2-1)
- Team C vs Team D (scheduled)
- Team E vs Team F (scheduled)
- Team G vs Team H (scheduled)

**Points** (after match completion):
- alice: 5 pts (exact match)
- bob: 3 pts (correct winner + 1 score)
- charlie: 1 pt (one score correct)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'app'` | Run `pytest` from project root (pytest.ini is there) |
| `Database locked` | Kill other connections: `rm worldcup.db && python3 scripts/seed_test_data.py` |
| `Connection refused` | Start backend: `python3 -m uvicorn app.main:app --port 8080` |
| Tests fail | Check admin email in `.env`: `ADMIN_EMAILS_STR=andertvistholm@live.dk` |

---

## File Locations

```
/home/anders/hello-scaleway/
├── run_e2e_tests.sh              ← Run this for quick test
├── league-standings.html          ← Open this in browser
├── scripts/seed_test_data.py      ← Create test data
├── tests/test_e2e_scenarios.py    ← Test suite
├── pytest.ini                     ← Pytest config
├── .env                           ← Admin email config
└── docs/
    ├── QUICK_START.md             ← This file
    ├── PROJECT_STATUS.md          ← Full overview
    ├── E2E_TESTING_SETUP.md        ← Detailed setup
    ├── E2E_TESTING_GUIDE.md        ← Testing guide
    ├── LEAGUE_STANDINGS_GUIDE.md   ← User guide
    └── ...
```

---

## Three Features at a Glance

### Feature 1: Admin Endpoint ✅
Update match results and auto-calculate scores.
```bash
# Admin can update match
curl -X PUT http://localhost:8080/matches/{id}/result \
  -d '{"home_score": 2, "away_score": 1}'
# Points auto-calculated for all predictions
```

### Feature 2: League Standings ✅
View real-time leaderboards with medals.
```bash
# Visit in browser
http://localhost:8080/league-standings.html
# Shows standings with 🥇🥈🥉 medals
```

### Feature 3: E2E Testing ✅
Test all scenarios without magic links.
```bash
# One command runs everything
bash run_e2e_tests.sh
# 7 tests pass ✅
```

---

## Configuration

Just one thing needed:

**`.env`** (already configured):
```env
ADMIN_EMAILS_STR=andertvistholm@live.dk
```

Everything else is automatic!

---

## Status

✅ **Admin Endpoint** - READY
✅ **Standings Frontend** - READY
✅ **E2E Tests** - READY
✅ **Documentation** - COMPLETE

🚀 **PROJECT READY FOR PRODUCTION**

---

## Next Steps

1. Run `bash run_e2e_tests.sh` to verify everything works
2. Check `PROJECT_STATUS.md` for full details
3. Deploy to production when ready

---

## Need More Info?

- **Setup**: See `E2E_TESTING_SETUP.md`
- **Testing**: See `E2E_TESTING_GUIDE.md`
- **Frontend**: See `LEAGUE_STANDINGS_GUIDE.md`
- **All Details**: See `PROJECT_STATUS.md`
- **Deployment**: See `ADMIN_ENDPOINT_DEPLOYMENT.md`

---

**Updated**: January 31, 2026
