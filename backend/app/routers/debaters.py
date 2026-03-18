from fastapi import APIRouter, Query
from ..database import get_pool
from ..queries import debater_queries as q
from ..cache import response_cache

router = APIRouter(tags=["debaters"])


@router.get("/debaters")
async def search_debaters(search: str = Query("", alias="q")):
    pool = await get_pool()
    if not search:
        rows = await pool.fetch(q.ALL_DEBATERS)
    else:
        rows = await pool.fetch(q.SEARCH_DEBATERS, f"%{search}%")
    return [dict(r) for r in rows]


@router.get("/debaters/{code}")
async def get_debater(code: str):
    cache_key = f"debaters:{code}"
    if cache_key in response_cache:
        return response_cache[cache_key]
    pool = await get_pool()
    row = await pool.fetchrow(q.CAREER_STATS, code)
    if not row:
        return {"error": "Debater not found"}
    result = dict(row)
    response_cache[cache_key] = result
    return result


@router.get("/debaters/{code}/season-summary")
async def get_season_summary(code: str):
    pool = await get_pool()
    rows = await pool.fetch(q.SEASON_SUMMARY, code)
    return [dict(r) for r in rows]


@router.get("/debaters/{code}/partners")
async def get_partners(code: str):
    pool = await get_pool()
    rows = await pool.fetch(q.PARTNER_HISTORY, code)
    return [dict(r) for r in rows]


@router.get("/debaters/{code}/tournaments")
async def get_tournaments(code: str):
    pool = await get_pool()
    rows = await pool.fetch(q.TOURNAMENT_LIST, code)
    return [dict(r) for r in rows]


@router.get("/debaters/{code}/tournaments/{tourn_id}/rounds")
async def get_tournament_rounds(code: str, tourn_id: int):
    pool = await get_pool()
    rows = await pool.fetch(q.TOURNAMENT_ROUNDS, code, tourn_id)
    return [dict(r) for r in rows]
