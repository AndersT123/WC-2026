# World Cup Prediction App

## Purpose
A web application that allows users to predict and place bets on the outcomes of games in the upcoming World Cup soccer tournament. The app uses a token-based betting system (no real money involved).

## Core Features

### User Management

#### Authentication: Magic Link (Passwordless)
- **No passwords required** - users authenticate via email magic links
- Prevents password reuse vulnerabilities
- Built-in email verification

**Sign-up flow:**
1. User provides username and email address
2. System sends magic link to email
3. User clicks link to verify email and complete registration
4. User receives initial token allocation and is logged in

**Login flow:**
1. User enters their email address
2. System sends magic link to email
3. User clicks link to log in
4. Session stored (e.g., 30 days) so they don't need to re-authenticate frequently

**Session management:**
- Logged-in sessions persist for extended period (30 days default)
- Users can log out manually
- Magic links expire after short time (15-30 minutes)
- One-time use tokens (link becomes invalid after use)

#### User Profile
- Username (chosen at sign-up)
- Email address (verified via magic link)
- Token balance(s)
- Betting history across all game modes
- League memberships
- Statistics and performance metrics

### Betting System - Three Game Modes

The app features three distinct sub-games for each match:

#### 1. Witt-Classic (Score Prediction Game)
- Users guess the exact score of the match (e.g., 2-1, 0-0, 3-2)
- Points awarded based on a specific point system
- Competitive scoring: more points for exact score vs. correct outcome
- All predictions compete against each other
- Leaderboard based on accumulated points across all matches

#### 2. Limit Order Book (Peer-to-Peer Betting Market)
- Users can act as market makers by posting "bets" with their own odds
- Other users can take/accept these bets (head-to-head betting)
- Order book displays available bets for each match outcome
- Players bet directly against each other (not against the house)
- Token transfer between winner and loser of each matched bet
- Similar to prediction markets or betting exchanges

#### 3. Traditional Betting with External Odds (Winner/Draw)
- Users bet on match outcome: Team A wins, Team B wins, or Draw
- Odds are sourced by scraping external betting providers
- Odds displayed to users before placing bets
- Payouts calculated based on the scraped odds
- System acts as the house for these bets

### General Betting Features
- View upcoming World Cup matches
- Track active bets across all three game modes
- View betting history for all game types
- Combined or separate token balances for each game mode (TBD)

### League System (Private Leagues Only)

**No global/public league** - all competition happens within private leagues

**League workflow:**
1. After email verification, users are prompted to either:
   - Create a new league (becomes league creator)
   - Join an existing league using a league code
2. Users must be in at least one league before they can place bets
3. Users can be members of multiple leagues simultaneously

**League creation:**
- Any registered user can create a league
- League creator provides:
  - League name
  - Optional description
- System generates unique league code (shareable)
- League code is visible in the UI for all members

**Joining leagues:**
- Users enter a league code to join
- Anyone with the league code can join (no approval needed)
- Can join at any time, even after tournament starts
- Late joiners receive default token allocation

**League standings:**
- Each league has its own leaderboard
- Users compete against others in the same league(s)
- Cross-league comparison not emphasized

### Token Economy
- Users receive initial token allocation when joining a league
- Late joiners get the same default amount (no penalty/catch-up)
- Tokens are used to place bets (not real money)
- Win tokens based on correct predictions
- Token economy details (shared vs per-league balances) - TBD

### Match/Game Data
- Display World Cup schedule
- Show match details (teams, date, time, location)
- Update match results
- Calculate bet outcomes based on actual results

## Technical Requirements

### Backend (FastAPI)
- RESTful API for all operations
- **Magic link authentication system**:
  - Generate secure one-time tokens
  - Send magic link emails
  - Validate and expire tokens
  - Session management (JWT or secure cookies)
- **Email service integration** (SendGrid, AWS SES, Mailgun, or SMTP)
- Database integration for:
  - Users and authentication (email, username, magic link tokens)
  - Matches/games schedule
  - Witt-Classic predictions and scoring
  - Limit order book (open orders, matched bets, order matching engine)
  - Traditional bets with external odds
  - Token balances (possibly separate for each game mode)
  - Match results and bet settlements
  - League data and memberships
- Authorization (users can only access their own bets)
- Web scraping service for external betting odds
- Order matching engine for limit order book
- Point calculation system for Witt-Classic
- Bet settlement and payout processing for all three modes

### Frontend
- Web interface for users to interact with the app
- Login/registration pages
- Match listing and betting interface
- User dashboard showing bets and tokens
- Leaderboard display

### Database
- Store user accounts and credentials
- Store match/game data (teams, date, time, results)
- Store Witt-Classic predictions and points earned
- Store limit order book data:
  - Open orders (posted bets awaiting takers)
  - Matched bets (completed peer-to-peer bets)
  - Order history
- Store traditional bets with external odds
- Track token balances per user (per game mode if separated)
- Store scraped odds data from external providers
- Transaction history for all token movements

### Deployment
- Hosted on Scaleway Serverless Containers
- Scalable to handle multiple concurrent users
- HTTPS enabled

## Current Progress
- ✅ FastAPI basic app created
- ✅ Docker containerization set up
- ✅ Scaleway Container Registry configured
- ✅ Successfully deployed to Scaleway Serverless Containers
- ✅ Public HTTPS endpoint available
- ✅ **MAGIC LINK AUTHENTICATION COMPLETE** (2026-01-31)

## ✅ AUTHENTICATION SYSTEM IMPLEMENTED (Jan 31, 2026)

### What Was Built Today
Complete passwordless authentication system with magic links:

**Project Structure:**
- Migrated from single `main.py` to modular architecture
- Created `app/` directory with proper separation of concerns
- 17 new files including models, services, routers, schemas

**Database:**
- ✅ User model (username, email, timestamps, last_login)
- ✅ MagicLinkToken model (tokens, expiration, one-time use)
- ✅ Alembic migrations configured and tested
- ✅ Async SQLAlchemy with SQLite (dev) / PostgreSQL (production) support

**API Endpoints Working:**
- ✅ POST /auth/signup - Create account & send magic link
- ✅ POST /auth/login - Send magic link to existing users
- ✅ GET /auth/verify - Verify token & authenticate (handles both signup & login)
- ✅ POST /auth/refresh - Refresh access token
- ✅ POST /auth/logout - Clear authentication cookies
- ✅ GET /auth/me - Get current user (protected endpoint)

**Security Features:**
- ✅ JWT access tokens (2 hours) + refresh tokens (30 days)
- ✅ httpOnly cookies for XSS protection
- ✅ Secure token generation (secrets.token_urlsafe with 256-bit entropy)
- ✅ Token expiration (15 minutes for magic links)
- ✅ One-time use tokens
- ✅ Rate limiting (3 requests/15min on signup/login)
- ✅ CORS configuration
- ✅ Input validation with Pydantic

**Services:**
- ✅ Email service with SendGrid integration (graceful fallback for dev)
- ✅ Token generation and validation service
- ✅ JWT authentication service
- ✅ Background cleanup task for expired tokens

**Testing:**
- ✅ All 7 authentication flows tested and passing
- ✅ Integration tests with httpx
- ✅ Signup → Verify → Protected endpoint → Login → Logout all working

**Documentation:**
- ✅ IMPLEMENTATION_SUMMARY.md with full details
- ✅ .env.example with all required variables
- ✅ Test scripts (test_app.py, test_endpoints.py)

### Where We Left Off (Ready to Resume)

**What Works:**
- Complete authentication system
- Database models and migrations
- All auth endpoints tested and functional
- Ready for production deployment

**Ready for Deployment:**
Need to set these environment variables on Scaleway:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/worldcup
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
SENDGRID_API_KEY=SG.xxx
FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=https://nswccycf3t1n-container-wc.functions.fnc.fr-par.scw.cloud
```

Then:
1. Update Scaleway container with new Docker image
2. Run `alembic upgrade head` to create database tables
3. Test production authentication flow

**Known Issues:**
- None! All tests passing

**Next Session - Start Here:**
You have two options:

**Option A: Deploy Authentication to Production**
1. Configure Scaleway managed PostgreSQL database
2. Set environment variables on Scaleway container
3. Build & push updated Docker image
4. Deploy and test production auth flow
5. Get SendGrid configured for real emails

**Option B: Continue Building Features Locally**
Start implementing the next major features:

## Next Steps (Priority Order)
1. ✅ ~~Implement user authentication system~~ **COMPLETE**
2. **League System** - Create/join private leagues
   - League model (name, code, creator, members)
   - POST /leagues - Create league & generate code
   - POST /leagues/join - Join league with code
   - GET /leagues - List user's leagues
   - GET /leagues/{id}/members - View league members
3. **Token/Balance System** - Track tokens per user per league
   - UserLeagueBalance model
   - Initial token allocation on league join
   - Token transaction history
4. **Match Management** - World Cup schedule
   - Match model (teams, date, venue, status, result)
   - Import/seed match data
   - GET /matches - List upcoming matches
   - Admin endpoints to update results
5. **Witt-Classic Mode** - Score prediction game
   - Prediction model
   - POST /predictions - Submit score guess
   - Point calculation engine
   - GET /leaderboard/{league_id} - League standings
6. **Limit Order Book** - Peer-to-peer betting
   - Order model (maker, taker, odds, stake, status)
   - Order matching engine
   - POST /orders - Create order
   - POST /orders/{id}/take - Accept bet
   - GET /orders/{match_id} - View order book
7. **Traditional Betting** - External odds
   - Bet model
   - Odds scraping service
   - POST /bets - Place bet
   - GET /odds/{match_id} - View available odds
8. Build frontend interface
9. Testing and deployment

**Files to Reference:**
- `IMPLEMENTATION_SUMMARY.md` - Complete auth system documentation
- `app/` - All application code
- `alembic/` - Database migrations
- `test_endpoints.py` - Test examples

## Deployment Info
- **Platform**: Scaleway Serverless Containers
- **Current URL**: https://nswccycf3t1n-container-wc.functions.fnc.fr-par.scw.cloud
- **Registry**: rg.fr-par.scw.cloud/fastapi-apps/fastapi-app:latest
- **Region**: fr-par (Paris)
