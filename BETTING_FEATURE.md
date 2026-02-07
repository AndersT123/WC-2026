# Betting Module - Complete Implementation

## Overview
A moneyline betting system where users can place bets on match outcomes (Home Win, Draw, Away Win) with real-time odds and automatic settlement.

## Features Implemented

### 1. **Database Models**
- **Bet** - User bets with outcomes, stakes, odds, and settlement
- **UserBalance** - Wallet tracking: balance, total wagered, total winnings
- Automatic relationships in User model

### 2. **Betting Logic**
- Place bets on upcoming matches only
- Real-time odds (mock data, ready for real API integration)
- Automatic balance deduction when bet placed
- Prevent negative balance (insufficient funds check)

### 3. **Bet Settlement**
- Automatic settlement when match result is entered
- Payout calculation based on odds
- Push (refund) on draw when betting win/loss
- Auto-return winnings to user balance

### 4. **API Endpoints**

#### Get Match Odds
```
GET /bets/match/{match_id}/odds
```
Returns betting odds for all outcomes.

#### Place Bet
```
POST /bets
{
  "match_id": "uuid",
  "league_id": "uuid",
  "outcome": "home_win|draw|away_win",
  "stake": 100.0
}
```
Returns: Placed bet details with potential payout

#### Get User Balance
```
GET /bets/balance
```
Returns: Current balance, total wagered, total winnings

#### Get User Bets
```
GET /bets
GET /bets?status=pending|won|lost|push
GET /bets/league/{league_id}
```
Returns: Bet history with match details

### 5. **Bet Status Lifecycle**
- **PENDING** - Bet placed, match not yet played
- **WON** - Bet outcome matched actual result
- **LOST** - Bet outcome didn't match
- **PUSH** - Refund on draw (bettor selected win/loss)

## Database Schema

```
bets
├── id (UUID)
├── user_id (FK)
├── match_id (FK)
├── league_id (FK)
├── outcome (home_win, draw, away_win)
├── stake (amount wagered)
├── odds (odds at time of bet)
├── potential_payout (stake × odds)
├── status (pending, won, lost, push)
├── actual_payout (if won/pushed)
├── created_at
└── settled_at

user_balance
├── id (UUID)
├── user_id (FK, unique)
├── balance (current balance)
├── total_wagered
├── total_winnings
├── created_at
└── updated_at
```

## Mock Odds (Ready for Real API)
Currently using mock odds in `app/services/bet_service.py`:
- Home Win: 2.0 (50% implied probability)
- Draw: 3.5 (28.6% implied probability)
- Away Win: 3.0 (33.3% implied probability)

**To use real odds:** Replace `get_match_odds()` function with API call to:
- The Odds API
- SofaScore
- Pinnacle
- Or any other odds provider

## Key Business Logic

### 1. Placing a Bet
- Check match status (must be "scheduled")
- Check user balance ≥ stake
- Deduct stake from balance
- Store bet as PENDING

### 2. Settling a Bet
- Admin enters match result
- System determines outcome (HOME_WIN, DRAW, AWAY_WIN)
- For each pending bet:
  - If outcome matches: status = WON, add payout to balance
  - If drew but bet on win/loss: status = PUSH, refund stake
  - Otherwise: status = LOST, payout = 0

### 3. User Balance
- Initial balance: $1000 (configurable)
- Decreases when placing bet
- Increases when bet wins or pushes
- Tracks cumulative stats

## Integration Points

### With Predictions
- Separate from prediction system (independent)
- Both track match outcomes
- Can have both bet + prediction on same match
- Both contribute to league leaderboard

### With Matches
- Bets link to Match model
- When match result updated, bets auto-settle
- Can only bet on "scheduled" matches

### With Leagues
- Bets are league-specific
- User can have different bets in different leagues
- Bets contribute to league statistics

## Exception Handling
- `InsufficientFundsError` - Balance too low
- `InvalidInputError` - Invalid outcome or match status
- `MatchNotFoundError` - Match doesn't exist
- Standard HTTP 400/422/404 responses

## Testing Scenarios

### Scenario 1: Winning Bet
1. User balance: $1000
2. Place $100 bet on Home Win (odds 2.0)
3. Potential payout shown: $200
4. Match result: Home Win
5. Bet settled as WON
6. New balance: $1100 ($1000 - $100 stake + $200 payout)

### Scenario 2: Lost Bet
1. User balance: $1100
2. Place $50 bet on Draw (odds 3.5)
3. Potential payout: $175
4. Match result: Home Win
5. Bet settled as LOST
6. New balance: $1100 (balance unchanged, stake already deducted)

### Scenario 3: Push (Refund)
1. User balance: $1100
2. Place $75 bet on Home Win (odds 2.0)
3. Match result: Draw
4. Bet settled as PUSH
5. Refund $75 to balance
6. New balance: $1100

## Next Steps

1. **Frontend Betting Page** - Create UI for:
   - View match odds
   - Place bet form
   - Bet history/slip
   - Balance display

2. **Real Odds Integration** - Replace mock odds with actual API

3. **Parlay Support** - Allow multiple selections per bet slip

4. **Betting Limits** - Add daily/weekly limits, max bet amounts

5. **Promotions** - Add bonus bets, free bets, boosts

6. **Leaderboard** - Show top bettors by profit/ROI

## Files Created/Modified

**New Files:**
- `app/models/bet.py` - Bet and UserBalance models
- `app/schemas/bet.py` - Bet request/response schemas
- `app/services/bet_service.py` - Betting business logic
- `app/routers/bets.py` - Betting API endpoints

**Modified Files:**
- `app/models/user.py` - Added bet/balance relationships
- `app/exceptions.py` - Added betting exceptions
- `app/database.py` - Import bet models
- `app/main.py` - Register bets router
- `app/routers/__init__.py` - Export bets router
