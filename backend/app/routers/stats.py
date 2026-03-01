from fastapi import APIRouter
from ..database import get_pool
from ..queries import stats_queries as q

router = APIRouter(tags=["stats"])


@router.get("/stats/overview")
async def get_overview():
    pool = await get_pool()
    row = await pool.fetchrow(q.OVERVIEW)
    return dict(row)
