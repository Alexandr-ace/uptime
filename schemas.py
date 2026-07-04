"""
Pydantic schemas для валидации входных и выходных данных
"""
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# ===== WEBSITES =====

class WebsiteCreate(BaseModel):
    """Что нужно для создания сайта."""
    url: HttpUrl
    name: str = Field(..., min_length=1, max_length=255)
    check_interval: int = Field(60, ge=10, description="Интервал в секундах")


class WebsiteUpdate(BaseModel):
    """Что можно обновить у сайта."""
    name: str | None = Field(None, min_length=1, max_length=255)
    check_interval: int | None = Field(None, ge=10)
    is_active: bool | None = None


class WebsiteResponse(BaseModel):
    """Что возвращаем пользователю."""
    id: int
    url: str
    name: str
    check_interval: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== CHECKS =====

class CheckCreate(BaseModel):
    """Что нужно для создания проверки."""
    status_code: int | None = None
    response_time: float | None = None
    is_success: bool
    error_message: str | None = None


class CheckResponse(BaseModel):
    """Что возвращаем пользователю."""
    id: int
    website_id: int
    status_code: int | None
    response_time: float | None
    is_success: bool
    error_message: str | None
    checked_at: datetime

    class Config:
        from_attributes = True