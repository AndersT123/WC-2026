import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.league import (
    CreateLeagueRequest,
    JoinLeagueRequest,
    LeagueResponse,
    LeagueWithMemberCount,
)
from app.services.league_service import (
    create_league,
    join_league,
    get_user_leagues,
    get_league_by_id,
    get_league_member_count,
    delete_league,
)

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("", response_model=List[LeagueWithMemberCount])
async def list_user_leagues(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[LeagueWithMemberCount]:
    """Get all leagues the current user is a member of."""
    leagues = await get_user_leagues(db, user.id)
    result = []
    for league in leagues:
        member_count = await get_league_member_count(db, league.id)
        result.append(
            LeagueWithMemberCount(
                **{**league.__dict__, "member_count": member_count}
            )
        )
    return result


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_new_league(
    request: CreateLeagueRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueResponse:
    """Create a new league (auto-joins creator)."""
    league = await create_league(
        db,
        name=request.name,
        creator_id=user.id,
        description=request.description,
    )
    await db.commit()
    await db.refresh(league)
    return LeagueResponse.model_validate(league)


@router.post("/join", response_model=LeagueResponse, status_code=status.HTTP_200_OK)
async def join_new_league(
    request: JoinLeagueRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueResponse:
    """Join a league with code."""
    league = await join_league(db, user.id, request.code)
    await db.commit()
    await db.refresh(league)
    return LeagueResponse.model_validate(league)


@router.delete("/{league_id}", status_code=204)
async def delete_league_endpoint(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a league. Only the creator can do this."""
    await delete_league(db, league_id, user.id)
    await db.commit()


@router.get("/{league_id}", response_model=LeagueWithMemberCount)
async def get_league_details(
    league_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueWithMemberCount:
    """Get league details (must be a member)."""
    # This endpoint doesn't enforce membership check - it's for exploring
    # Frontend should handle membership validation
    league = await get_league_by_id(db, league_id)
    member_count = await get_league_member_count(db, league_id)
    return LeagueWithMemberCount(
        **{**league.__dict__, "member_count": member_count}
    )
