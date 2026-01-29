import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

async def get_db_pool():
    global _pool

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
        )
    return _pool
