from typing import Optional, List, Any

import asyncpg

from config import settings
from logger import get_logger

logger = get_logger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def create_db_pool() -> None:
    """Create the async database connection pool."""
    global _pool
    _pool = await asyncpg.create_pool(
        host=settings.POSTGRES_DB_HOST,
        port=settings.POSTGRES_DB_PORT,
        database=settings.POSTGRES_DB_NAME,
        user=settings.POSTGRES_DB_USER,
        password=settings.POSTGRES_DB_PASSWORD,
        min_size=2,
        max_size=10,
    )
    logger.info("Database connection pool created")


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


def _get_pool() -> asyncpg.Pool:
    """Get the current connection pool or raise."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call create_db_pool() first.")
    return _pool


async def execute_query(query: str, *args: Any) -> List[asyncpg.Record]:
    """Execute a SELECT query and return multiple rows."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute_query_one(query: str, *args: Any) -> Optional[asyncpg.Record]:
    """Execute a SELECT query and return a single row."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute_command(query: str, *args: Any) -> str:
    """Execute an INSERT/UPDATE/DELETE command."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def execute_command_with_return(query: str, *args: Any) -> Optional[asyncpg.Record]:
    """Execute an INSERT/UPDATE with RETURNING clause."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
