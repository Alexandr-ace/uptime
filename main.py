"""
Uptime Monitor - Фаза 2 (asyncpg + чистый SQL)
"""
import asyncpg
from dotenv import load_dotenv
import os
import asyncio
import time

# Загружаем переменные из .env
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
        # Таблица сайтов
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

        # Таблица проверок
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


async def create_website(url: str, name: str, check_interval: int = 60):
    """Создаёт новый сайт."""
    conn = await get_connection()
    try:
        website = await conn.fetchrow(
            """
            INSERT INTO websites (url, name, check_interval)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            url, name, check_interval
        )
        print(f"✅ Сайт создан: {dict(website)}")
        return website
    finally:
        await conn.close()


async def get_all_websites():
    """Получает все сайты."""
    conn = await get_connection()
    try:
        websites = await conn.fetch("SELECT * FROM websites ORDER BY created_at DESC")
        print(f"📋 Найдено сайтов: {len(websites)}")
        for site in websites:
            status = '✓' if site['is_active'] else '○'
            print(
                f"  - [{site['id']}] {site['name']} ({site['url']}) [{status}]")
        return websites
    finally:
        await conn.close()


async def get_website_by_id(website_id: int):
    """Получает сайт по ID."""
    conn = await get_connection()
    try:
        website = await conn.fetchrow("SELECT * FROM websites WHERE id = $1", website_id)
        if website:
            print(f"📋 Сайт [{website['id']}]: {website['name']}")
        else:
            print(f"❌ Сайт с ID {website_id} не найден")
        return website
    finally:
        await conn.close()


async def update_website(website_id: int, name: str = None, is_active: bool = None):
    """Обновляет сайт."""
    conn = await get_connection()
    try:
        updates = []
        values = []
        param_num = 1

        if name is not None:
            updates.append(f"name = ${param_num}")
            values.append(name)
            param_num += 1

        if is_active is not None:
            updates.append(f"is_active = ${param_num}")
            values.append(is_active)
            param_num += 1

        if not updates:
            print("❌ Нечего обновлять")
            return None

        values.append(website_id)
        query = f"UPDATE websites SET {', '.join(updates)} WHERE id = ${param_num} RETURNING *"

        website = await conn.fetchrow(query, *values)

        if website:
            print(f"✅ Сайт обновлён: {dict(website)}")
        else:
            print(f"❌ Сайт с ID {website_id} не найден")

        return website
    finally:
        await conn.close()


async def delete_website(website_id: int):
    """Удаляет сайт."""
    conn = await get_connection()
    try:
        result = await conn.fetchval("DELETE FROM websites WHERE id = $1 RETURNING id", website_id)

        if result:
            print(f"✅ Сайт {website_id} удалён")
        else:
            print(f"❌ Сайт с ID {website_id} не найден")

        return result
    finally:
        await conn.close()


async def create_check(website_id: int, status_code: int, response_time: float, is_success: bool, error_message: str = None):
    """Создаёт запись о проверке."""
    conn = await get_connection()
    try:
        check = await conn.fetchrow(
            """
            INSERT INTO checks (website_id, status_code, response_time, is_success, error_message)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            website_id, status_code, response_time, is_success, error_message
        )
        print(f"✅ Проверка создана: {dict(check)}")
        return check
    finally:
        await conn.close()


async def get_checks_for_website(website_id: int, limit: int = 5):
    """Получает историю проверок сайта."""
    conn = await get_connection()
    try:
        checks = await conn.fetch(
            """
            SELECT * FROM checks
            WHERE website_id = $1
            ORDER BY checked_at DESC
            LIMIT $2
            """,
            website_id, limit
        )
        print(f"📋 Найдено проверок: {len(checks)}")
        for check in checks:
            status = '✓' if check['is_success'] else '✗'
            print(
                f"  - [{check['id']}] Статус: {check['status_code']}, Время: {check['response_time']:.2f}с [{status}]")
        return checks
    finally:
        await conn.close()


async def main():
    """Основная функция."""
    print("\n" + "="*60)
    print("🚀 Uptime Monitor - Фаза 2 (asyncpg)")
    print("="*60 + "\n")

    start_time = time.time()

    # 1. Инициализация БД
    await init_db()

    # 2. CREATE - создаём сайты
    print("\n🌐 Создаём сайты...")
    await create_website("https://google.com", "Google", 60)
    await create_website("https://github.com", "GitHub", 120)
    await create_website("https://python.org", "Python", 300)

    # 3. READ - получаем все сайты
    print("\n📋 Все сайты:")
    await get_all_websites()

    # 4. READ - получаем сайт по ID
    print("\n🔍 Получаем сайт по ID:")
    await get_website_by_id(1)

    # 5. UPDATE - обновляем сайт
    print("\n✏️ Обновляем сайт:")
    await update_website(1, is_active=False)

    # 6. READ - проверяем обновление
    print("\n📋 Все сайты после обновления:")
    await get_all_websites()

    # 7. CREATE - создаём проверки
    print("\n🔍 Создаём проверки...")
    await create_check(1, 200, 0.45, True)
    await create_check(1, 200, 0.52, True)
    await create_check(1, 503, 2.1, False, "Service unavailable")

    # 8. READ - получаем историю проверок
    print("\n📋 История проверок для сайта 1:")
    await get_checks_for_website(1)

    # 9. DELETE - удаляем сайт
    print("\n🗑️ Удаляем сайт:")
    await delete_website(2)

    # 10. READ - проверяем удаление
    print("\n📋 Все сайты после удаления:")
    await get_all_websites()

    total_time = time.time() - start_time

    print("\n" + "="*60)
    print(f"✅ Фаза 2 завершена за {total_time:.2f}с")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
