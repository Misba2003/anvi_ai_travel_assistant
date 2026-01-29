from services.db import get_db_pool

MAX_HISTORY = 10


async def save_message(app_user_id: str, role: str, content: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO chat_messages (app_user_id, role, content)
            VALUES ($1, $2, $3)
            """,
            app_user_id,
            role,
            content
        )


async def get_recent_messages(app_user_id: str, limit: int = MAX_HISTORY):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content
            FROM chat_messages
            WHERE app_user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            app_user_id,
            limit
        )

    return [
        {"role": r["role"], "content": r["content"]}
        for r in reversed(rows)
    ]
