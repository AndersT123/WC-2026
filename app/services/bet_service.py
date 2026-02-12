"""Betting service for handling bets and odds."""

import uuid
from decimal import Decimal
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bet import Bet, BetOutcome, BetStatus
from app.models.match import Match
from app.models.user import User
from app.schemas.bet import PlaceBetRequest, MatchOdds, BetOutcomeOdds
from app.exceptions import InvalidInputError


# Mock odds for testing - in production, fetch from external API
MOCK_ODDS = {
    "home_win": 2.0,
    "draw": 3.5,
    "away_win": 3.0,
}


async def get_match_odds(db: AsyncSession, match: Match) -> MatchOdds:
    """Get odds for a match (currently mock data, integrate real API here)."""
    outcomes = []

    for outcome_name, odds in MOCK_ODDS.items():
        # Calculate implied probability from odds
        # Probability = 1 / odds
        implied_prob = (1 / odds) * 100

        outcomes.append(
            BetOutcomeOdds(
                outcome=outcome_name,
                odds=odds,
                implied_probability=round(implied_prob, 2),
            )
        )

    return MatchOdds(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        match_datetime=match.match_datetime,
        outcomes=outcomes,
    )


async def place_bet(
    db: AsyncSession,
    user_id: uuid.UUID,
    match_id: uuid.UUID,
    outcome: str,
) -> Bet:
    """Place a bet on a match outcome. Bet applies to all leagues user is in."""

    # Validate outcome
    if outcome not in [e.value for e in BetOutcome]:
        raise InvalidInputError(f"Invalid outcome: {outcome}")

    # Get match and verify it's scheduled
    match = await db.get(Match, match_id)
    if not match:
        raise InvalidInputError("Match not found")

    if match.status != "scheduled":
        raise InvalidInputError("Cannot bet on non-scheduled matches")

    # Check for existing bet (unique constraint)
    existing_bet = await db.execute(
        select(Bet)
        .where(Bet.user_id == user_id)
        .where(Bet.match_id == match_id)
    )
    if existing_bet.scalar_one_or_none():
        raise InvalidInputError("You have already placed a bet on this match")

    # Get odds
    match_odds = await get_match_odds(db, match)
    odds_for_outcome = next(
        (o.odds for o in match_odds.outcomes if o.outcome == outcome),
        None
    )

    if not odds_for_outcome:
        raise InvalidInputError(f"No odds available for {outcome}")

    # Create bet (always 1 token, no balance check)
    bet = Bet(
        user_id=user_id,
        match_id=match_id,
        outcome=outcome,
        odds=odds_for_outcome,
        status=BetStatus.PENDING,
    )

    db.add(bet)
    await db.flush()

    return bet


async def settle_bets(
    db: AsyncSession,
    match_id: uuid.UUID,
    home_score: int,
    away_score: int,
) -> int:
    """Settle all bets for a match based on final score."""

    # Determine actual outcome
    if home_score > away_score:
        actual_outcome = BetOutcome.HOME_WIN
    elif away_score > home_score:
        actual_outcome = BetOutcome.AWAY_WIN
    else:
        actual_outcome = BetOutcome.DRAW

    # Get all pending bets for this match
    result = await db.execute(
        select(Bet)
        .where(Bet.match_id == match_id)
        .where(Bet.status == BetStatus.PENDING)
    )
    bets = result.scalars().all()

    for bet in bets:
        bet.settled_at = datetime.utcnow()

        # Calculate payout
        if bet.outcome == actual_outcome.value:
            # WIN: 1 × odds (decimal)
            bet.status = BetStatus.WON
            bet.actual_payout = 1.0 * bet.odds

        elif bet.outcome == "draw" and actual_outcome != BetOutcome.DRAW:
            # Bet draw, didn't draw = LOSS
            bet.status = BetStatus.LOST
            bet.actual_payout = 0.0

        elif bet.outcome in ["home_win", "away_win"] and actual_outcome == BetOutcome.DRAW:
            # Bet win, but drew = PUSH (refund)
            bet.status = BetStatus.PUSH
            bet.actual_payout = 1.0

        else:
            # LOSS
            bet.status = BetStatus.LOST
            bet.actual_payout = 0.0

    return len(bets)


async def get_user_bets(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str = None,
) -> List[Bet]:
    """Get user's bets with optional filters."""
    query = select(Bet).where(Bet.user_id == user_id)

    if status:
        query = query.where(Bet.status == status)

    result = await db.execute(query.order_by(Bet.created_at.desc()))
    return result.scalars().all()


