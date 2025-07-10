from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any


class ComplaintCreate(BaseModel):
    text: str = Field(
        ...,
        max_length=2000,
        description="Текст жалобы клиента",
        examples=["Не приходит SMS-код для входа в приложение"]
    )


    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError('Текст жалобы не может состоять только из пробелов')
        return cleaned


class ComplaintResponse(BaseModel):
    """Схема ответа с данными жалобы"""
    id: int = Field(
        ...,
        description="Уникальный идентификатор жалобы",
        examples=[123]
    )
    status: str = Field(
        ...,
        description="Статус обработки жалобы",
        examples=["open"]
    )
    sentiment: Optional[str] = Field(
        None,
        description="Тональность жалобы (positive/negative/neutral/unknown)",
        examples=["negative"]
    )
    category: Optional[str] = Field(
        None,
        description="Категория жалобы (техническая/оплата/другое)",
        examples=["техническая"]
    )



class ComplaintResponseWorkflow(ComplaintResponse):
    timestamp: datetime = Field(
        ...,
        description="Время создания жалобы",
        examples=["2025-07-08T10:30:00Z"]
    )
    text: Optional[str] = Field(
        None,
        description="Текст жалобы (опционально)",
        examples=["Не приходит SMS-код для входа в приложение"]
    )
    is_spam: Optional[bool] = Field(
        None,
        description="Результат проверки на спам",
        examples=[False]
    )
    ip_location: Optional[str] = Field(
        None,
        description="Геолокация по IP адресу",
        examples=["Moscow, Russia"]
    )

class ComplaintList(BaseModel):
    """Схема для списка жалоб"""
    complaints: List[ComplaintResponseWorkflow] = Field(
        ...,
        description="Список жалоб"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Общее количество жалоб",
        examples=[150]
    )
    page: int = Field(
        ...,
        ge=1,
        description="Текущая страница",
        examples=[1]
    )
    per_page: int = Field(
        ...,
        ge=1,
        le=100,
        description="Количество элементов на странице",
        examples=[20]
    )


class ComplaintStatusUpdate(BaseModel):
    """Схема для обновления статуса жалобы"""
    status: str = Field(
        ...,
        pattern="^(open|closed)$",
        description="Новый статус жалобы",
        examples=["closed"]
    )


class HealthCheck(BaseModel):
    """Схема для проверки здоровья системы"""
    status: str = Field(
        ...,
        description="Общий статус системы",
        examples=["healthy"]
    )
    timestamp: str = Field(
        ...,
        description="Время проверки в ISO формате",
        examples=["2025-07-08T10:30:00Z"]
    )
    services: Dict[str, Any] = Field(
        ...,
        description="Статус отдельных сервисов",
        examples=[{
            "database": "healthy",
            "sentiment_api": "healthy",
            "openai_api": "degraded"
        }]
    )


class ErrorResponse(BaseModel):
    """Схема для ответов об ошибках"""
    detail: str = Field(
        ...,
        description="Описание ошибки",
        examples=["Complaint not found"]
    )
    timestamp: str = Field(
        ...,
        description="Время возникновения ошибки",
        examples=["2025-07-08T10:30:00Z"]
    )
    error_code: Optional[str] = Field(
        None,
        description="Код ошибки для программной обработки",
        examples=["COMPLAINT_NOT_FOUND"]
    )


class ComplaintFilter(BaseModel):
    """Схема для фильтрации жалоб"""
    status: Optional[str] = Field(
        None,
        pattern="^(open|closed)$",
        description="Фильтр по статусу",
        examples=["open"]
    )
    since_hours: Optional[int] = Field(
        None,
        ge=1,
        le=8760,  # Максимум год
        description="Жалобы за последние N часов",
        examples=[24]
    )
    category: Optional[str] = Field(
        None,
        pattern="^(техническая|оплата|другое)$",
        description="Фильтр по категории",
        examples=["техническая"]
    )
    sentiment: Optional[str] = Field(
        None,
        pattern="^(positive|negative|neutral|unknown)$",
        description="Фильтр по тональности",
        examples=["negative"]
    )
    limit: Optional[int] = Field(
        20,
        ge=1,
        le=100,
        description="Лимит количества результатов",
        examples=[20]
    )
    offset: Optional[int] = Field(
        0,
        ge=0,
        description="Смещение для пагинации",
        examples=[0]
    )