from fastapi import APIRouter, Query
from ..database import get_pool
from ..queries import tournament_queries as q

router = APIRouter(tags=["tournaments"])


@router.get("/tournaments/seasons")
async def get_seasons():
    pool = await get_pool()
    rows = await pool.fetch(q.SEASONS)
    return [r["season"] for r in rows]


@router.get("/tournaments")
async def search_tournaments(
    search: str = Query(None, alias="q"),
    season: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    pool = await get_pool()
    search_param = f"%{search}%" if search else None
    offset = (page - 1) * per_page
    rows = await pool.fetch(q.SEARCH_TOURNAMENTS, search_param, season, per_page, offset)
    count_row = await pool.fetchrow(q.COUNT_TOURNAMENTS, search_param, season)
    total = count_row["total"]
    return {
        "results": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/tournaments/{tournament_id}")
async def get_tournament(tournament_id: int):
    pool = await get_pool()
    row = await pool.fetchrow(q.TOURNAMENT_DETAIL, tournament_id)
    if not row:
        return {"error": "Tournament not found"}
    return dict(row)


@router.get("/tournaments/{tournament_id}/standings")
async def get_standings(tournament_id: int):
    pool = await get_pool()
    rows = await pool.fetch(q.STANDINGS, tournament_id)
    return [dict(r) for r in rows]


@router.get("/tournaments/{tournament_id}/elims")
async def get_elims(tournament_id: int):
    pool = await get_pool()
    rows = await pool.fetch(q.ELIM_RESULTS, tournament_id)
    return [dict(r) for r in rows]


@router.get("/tournaments/{tournament_id}/rounds")
async def get_rounds(tournament_id: int):
    pool = await get_pool()
    rows = await pool.fetch(q.ROUND_LIST, tournament_id)
    return [dict(r) for r in rows]


@router.get("/tournaments/{tournament_id}/rounds/{round_number}")
async def get_round_results(tournament_id: int, round_number: str):
    pool = await get_pool()
    rows = await pool.fetch(q.ROUND_RESULTS, tournament_id, round_number)
    return [dict(r) for r in rows]


@router.get("/tournaments/{tournament_id}/teams/{team_id}")
async def get_team_rounds(tournament_id: int, team_id: int):
    pool = await get_pool()
    rows = await pool.fetch(q.TEAM_ROUNDS, team_id, tournament_id)
    return [dict(r) for r in rows]


@router.get("/teams")
async def search_teams(
    search: str = Query(..., alias="q"),
    year: int = Query(None),
):
    pool = await get_pool()
    rows = await pool.fetch(q.TEAM_SEARCH, f"%{search}%", year)
    return [dict(r) for r in rows]
