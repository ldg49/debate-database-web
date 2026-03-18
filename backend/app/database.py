import asyncpg
from .config import DATABASE_URL, DATABASE_READONLY_URL

pool: asyncpg.Pool | None = None
write_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Read-only connection pool (uses DATABASE_READONLY_URL)."""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_READONLY_URL, min_size=2, max_size=10)
    return pool


async def get_write_pool() -> asyncpg.Pool:
    """Small write pool for ai_query_log inserts (uses DATABASE_URL)."""
    global write_pool
    if write_pool is None:
        write_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)
    return write_pool


async def close_pool():
    global pool, write_pool
    if pool:
        await pool.close()
        pool = None
    if write_pool:
        await write_pool.close()
        write_pool = None
