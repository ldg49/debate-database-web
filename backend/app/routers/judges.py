from fastapi import APIRouter, Query
from ..database import get_pool
from ..queries import judge_queries as q

router = APIRouter(tags=["judges"])


@router.get("/judges")
async def search_judges(search: str = Query("", alias="q")):
    pool = await get_pool()
    if not search:
        return []
    rows = await pool.fetch(q.SEARCH_JUDGES, f"%{search}%")
    return [dict(r) for r in rows]


@router.get("/judges/{name}")
async def get_judge(name: str):
    pool = await get_pool()
    row = await pool.fetchrow(q.JUDGE_CAREER, name)
    if not row:
        return {"error": "Judge not found"}
    return dict(row)


@router.get("/judges/{name}/season-summary")
async def get_judge_seasons(name: str):
    pool = await get_pool()
    rows = await pool.fetch(q.JUDGE_SEASON_SUMMARY, name)
    return [dict(r) for r in rows]


@router.get("/judges/{name}/tournaments")
async def get_judge_tournaments(name: str):
    pool = await get_pool()
    rows = await pool.fetch(q.JUDGE_TOURNAMENT_LIST, name)
    return [dict(r) for r in rows]


@router.get("/judges/{name}/tournaments/{tourn_id}/rounds")
async def get_judge_tournament_rounds(name: str, tourn_id: int):
    pool = await get_pool()
    rows = await pool.fetch(q.JUDGE_TOURNAMENT_ROUNDS, name, tourn_id)
    return [dict(r) for r in rows]
