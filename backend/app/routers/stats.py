from fastapi import APIRouter
from ..database import get_pool
from ..queries import stats_queries as q
from ..cache import response_cache

router = APIRouter(tags=["stats"])


@router.get("/stats/overview")
async def get_overview():
    cache_key = "stats:overview"
    if cache_key in response_cache:
        return response_cache[cache_key]
    pool = await get_pool()
    row = await pool.fetchrow(q.OVERVIEW)
    result = dict(row)
    response_cache[cache_key] = result
    return result
