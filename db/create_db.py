import asyncio
import os
import sys
import psycopg
from psycopg import AsyncConnection


async def create_tables():
    conn: AsyncConnection = await psycopg.AsyncConnection.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "renal_database"),
        user=os.getenv("DB_USER", "renal"),
        password=os.getenv("DB_PASSWORD", "renal")
    )
    async with conn.cursor() as cur:
        await cur.execute('''
            CREATE TABLE IF NOT EXISTS chains (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(256),
                chain_size INT,
                rating FLOAT
            );
            CREATE TABLE IF NOT EXISTS places (
                id VARCHAR(128) PRIMARY KEY,
                name VARCHAR(256) NOT NULL,
                address VARCHAR(256),
                description TEXT,
                rating FLOAT NOT NULL,
                id_chain BIGINT NULL,
                bot_amount INT,
                spam_amount INT,
                inept_amount INT,
                LLM_amount INT,
                reviews_amount INT,
                CONSTRAINT fk_chain FOREIGN KEY (id_chain) REFERENCES chains (id)
            );
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(128) PRIMARY KEY,
                name VARCHAR(256),
                bad_reviews INT,
                good_reviews INT,
                total_reviews INT,
                probability_bad FLOAT
                -- TODO: Придумать подсчет вероятности того что пользователь бот
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id VARCHAR(128) PRIMARY KEY,
                id_place VARCHAR(32) NOT NULL,
                id_user VARCHAR(32) NULL,
                feedback TEXT,
                date DATE,
                bot_prob FLOAT,
                spam_prob FLOAT,
                inept_prob FLOAT,
                LLM_prob FLOAT,
                score FLOAT,
                corrected_score FLOAT,
                CONSTRAINT fk_place FOREIGN KEY (id_place) REFERENCES places (id),
                CONSTRAINT fk_user FOREIGN KEY (id_user) REFERENCES users (id)
            );
        ''')
        await conn.commit()
    await conn.close()


if __name__ == '__main__':
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_tables())
