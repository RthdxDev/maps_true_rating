import asyncio
import os

import psycopg
import sys

# ✅ Добавляем эту строчку для Windows
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TABLES = [
    "reviews",
    "places",
    "chains",
    "users"
]


async def drop_tables():
    async with await psycopg.AsyncConnection.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "renal_database"),
            user=os.getenv("DB_USER", "renal"),
            password=os.getenv("DB_PASSWORD", "renal")
    ) as conn:
        async with conn.cursor() as cur:
            for table in TABLES:
                await cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"✅ Dropped table: {table}")
            await conn.commit()


if __name__ == "__main__":
    asyncio.run(drop_tables())
