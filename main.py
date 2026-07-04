"""
Uptime Monitor API - Фаза 4 (FastAPI + asyncpg)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from database import get_connection, init_db
from schemas import (
    WebsiteCreate, WebsiteUpdate, WebsiteResponse,
    CheckCreate, CheckResponse
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """При запуске создаём таблицы."""
    print("🚀 Запуск Uptime Monitor API...")
    await init_db()
    yield
    print("👋 Остановка...")


app = FastAPI(
    title="Uptime Monitor API",
    description="Мониторинг доступности сайтов",
    version="1.0.0",
    lifespan=lifespan,
)


# ==============================
# WEBSITES
# ==============================

@app.get("/")
async def root():
    return {
        "message": "Uptime Monitor API",
        "docs": "/docs"
    }


@app.get("/websites", response_model=list[WebsiteResponse])
async def get_websites():
    """Получить все сайты."""
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM websites ORDER BY created_at DESC")
        return [dict(r) for r in rows]
    finally:
        await conn.close()


@app.get("/websites/{website_id}", response_model=WebsiteResponse)
async def get_website(website_id: int):
    """Получить сайт по ID."""
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM websites WHERE id = $1", website_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Сайт не найден")
        return dict(row)
    finally:
        await conn.close()


@app.post("/websites", response_model=WebsiteResponse, status_code=201)
async def create_website(data: WebsiteCreate):
    """Создать сайт для мониторинга."""
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO websites (url, name, check_interval)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            str(data.url), data.name, data.check_interval
        )
        return dict(row)
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Такой URL уже добавлен")
        raise
    finally:
        await conn.close()


@app.patch("/websites/{website_id}", response_model=WebsiteResponse)
async def update_website(website_id: int, data: WebsiteUpdate):
    """Обновить сайт."""
    conn = await get_connection()
    try:
        # Проверяем существование
        row = await conn.fetchrow(
            "SELECT * FROM websites WHERE id = $1", website_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Сайт не найден")

        # Строим динамический UPDATE
        updates = []
        values = []
        param = 1

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            updates.append(f"{field} = ${param}")
            values.append(value)
            param += 1

        if not updates:
            return dict(row)

        values.append(website_id)
        query = f"UPDATE websites SET {', '.join(updates)} WHERE id = ${param} RETURNING *"

        updated = await conn.fetchrow(query, *values)
        return dict(updated)
    finally:
        await conn.close()


@app.delete("/websites/{website_id}", status_code=204)
async def delete_website(website_id: int):
    """Удалить сайт."""
    conn = await get_connection()
    try:
        result = await conn.fetchval(
            "DELETE FROM websites WHERE id = $1 RETURNING id", website_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Сайт не найден")
    finally:
        await conn.close()


# ==============================
# CHECKS
# ==============================

@app.get("/websites/{website_id}/checks", response_model=list[CheckResponse])
async def get_checks(website_id: int, limit: int = 10):
    """Получить историю проверок сайта."""
    conn = await get_connection()
    try:
        # Проверяем, что сайт существует
        website = await conn.fetchrow(
            "SELECT id FROM websites WHERE id = $1", website_id
        )
        if not website:
            raise HTTPException(status_code=404, detail="Сайт не найден")

        rows = await conn.fetch(
            """
            SELECT * FROM checks
            WHERE website_id = $1
            ORDER BY checked_at DESC
            LIMIT $2
            """,
            website_id, limit
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


@app.post("/websites/{website_id}/checks", response_model=CheckResponse, status_code=201)
async def create_check(website_id: int, data: CheckCreate):
    """Добавить результат проверки."""
    conn = await get_connection()
    try:
        # Проверяем, что сайт существует
        website = await conn.fetchrow(
            "SELECT id FROM websites WHERE id = $1", website_id
        )
        if not website:
            raise HTTPException(status_code=404, detail="Сайт не найден")

        row = await conn.fetchrow(
            """
            INSERT INTO checks (website_id, status_code, response_time, is_success, error_message)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            website_id,
            data.status_code,
            data.response_time,
            data.is_success,
            data.error_message
        )
        return dict(row)
    finally:
        await conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)