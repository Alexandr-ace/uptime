"""
Подключение к БД через asyncpg
"""
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"📡 Подключаемся к: {DATABASE_URL}")


async def get_connection():
    """Создаёт подключение к БД."""
    return await asyncpg.connect(DATABASE_URL)


async def init_db():
    """Создаёт таблицы."""
    conn = await get_connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id SERIAL PRIMARY KEY,
                url VARCHAR(500) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                check_interval INTEGER DEFAULT 60,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id SERIAL PRIMARY KEY,
                website_id INTEGER NOT NULL,
                status_code INTEGER,
                response_time FLOAT,
                is_success BOOLEAN NOT NULL,
                error_message TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Таблицы созданы")
    finally:
        await conn.close()