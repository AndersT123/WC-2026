"""API routes for betting."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.bet import (
    PlaceBetRequest,
    BetResponse,
    MatchOdds,
    BetHistoryResponse,
)
from app.services.bet_service import (
    place_bet,
    get_user_bets,
    get_match_odds,
)
from app.models.match import Match

router = APIRouter(prefix="/bets", tags=["bets"])


@router.get("/match/{match_id}/odds", response_model=MatchOdds)
async def get_match_odds_endpoint(
    match_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchOdds:
    """Get betting odds for a match."""
    match = await db.get(Match, match_id)
    if not match:
        from app.exceptions import MatchNotFoundError
        raise MatchNotFoundError()

    return await get_match_odds(db, match)


@router.post("", response_model=BetResponse, status_code=status.HTTP_201_CREATED)
async def place_bet_endpoint(
    request: PlaceBetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BetResponse:
    """Place a bet on a match outcome."""
    bet = await place_bet(
        db,
        user.id,
        request.match_id,
        request.outcome,
    )
    await db.commit()
    await db.refresh(bet)
    return BetResponse.model_validate(bet)


@router.get("", response_model=List[BetHistoryResponse])
async def get_user_bets_endpoint(
    status: str = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BetHistoryResponse]:
    """Get user's bets with optional filters."""
    bets = await get_user_bets(db, user.id, status)

    # Convert to response with match details
    results = []
    for bet in bets:
        match = await db.get(Match, bet.match_id)
        if match:
            results.append(
                BetHistoryResponse(
                    id=bet.id,
                    match_id=bet.match_id,
                    home_team=match.home_team,
                    away_team=match.away_team,
                    outcome=bet.outcome,
                    tokens=3,
                    odds=bet.odds,
                    potential_payout=3.0 * bet.odds,
                    status=bet.status.value,
                    actual_payout=bet.actual_payout,
                    match_datetime=match.match_datetime,
                    created_at=bet.created_at,
                    settled_at=bet.settled_at,
                )
            )

    return results


@router.get("/league/{league_id}", response_model=List[BetHistoryResponse])
async def get_league_bets_endpoint(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BetHistoryResponse]:
    """Get user's bets. League parameter is ignored as bets apply to all leagues."""
    return await get_user_bets_endpoint(user=user, db=db)


@router.delete("/{bet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bet_endpoint(
    bet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user's bet."""
    from app.models.bet import Bet
    from app.exceptions import BetNotFoundError, ForbiddenError

    bet = await db.get(Bet, bet_id)
    if not bet:
        raise BetNotFoundError()

    if bet.user_id != user.id:
        raise ForbiddenError("You can only delete your own bets")

    await db.delete(bet)
    await db.commit()
