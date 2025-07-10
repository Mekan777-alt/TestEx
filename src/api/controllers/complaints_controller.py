from typing import List, Optional

from fastapi import Depends, APIRouter, Request, Query
from starlette import status

from api.dto.complaints_dto import (
    ComplaintResponse,
    ComplaintCreate,
    ComplaintList,
    ComplaintStatusUpdate
)
from api.services.complaints_service import ComplaintsService, get_complaints_service

router = APIRouter(
    prefix="/complaints",
    tags=["Обработка жалоб"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ComplaintResponse,
    summary="Создание новой жалобы",
    description="Создание новой жалобы с автоматическим анализом тональности и категоризацией через ИИ"
)
async def create_complaint(
        complaint: ComplaintCreate,
        request: Request,
        service: ComplaintsService = Depends(get_complaints_service)
) -> ComplaintResponse:
    """
    Создание новой жалобы с полной обработкой:
    - Анализ тональности через APILayer
    - Проверка на спам (Через background задачи)
    - Определение геолокации по IP
    - Категоризация через OpenAI (асинхронно)
    """
    return await service.create_complaint_service(complaint, request)


@router.get(
    "",
    response_model=ComplaintList,
    summary="Получение списка жалоб",
    description="Получение списка жалоб с возможностью фильтрации и пагинации"
)
async def get_complaints(
        status: Optional[str] = Query(None, description="Фильтр по статусу (open/closed)"),
        since_hours: Optional[int] = Query(None, description="Жалобы за последние N часов", ge=1, le=8760),
        category: Optional[str] = Query(None, description="Фильтр по категории"),
        sentiment: Optional[str] = Query(None, description="Фильтр по тональности"),
        limit: int = Query(20, description="Лимит результатов", ge=1, le=100),
        offset: int = Query(0, description="Смещение для пагинации", ge=0),
        service: ComplaintsService = Depends(get_complaints_service)
) -> ComplaintList:
    """
    Получение списка жалоб с фильтрацией.
    Используется n8n для автоматизации workflow.
    """
    return await service.get_complaints_list(
        status=status,
        since_hours=since_hours,
        category=category,
        sentiment=sentiment,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Получение жалобы по ID",
    description="Получение детальной информации о конкретной жалобе"
)
async def get_complaint(
        complaint_id: int,
        service: ComplaintsService = Depends(get_complaints_service)
) -> ComplaintResponse:
    """Получение конкретной жалобы по ID"""
    return await service.get_complaint_by_id(complaint_id)


@router.patch(
    "/{complaint_id}/status",
    summary="Обновление статуса жалобы",
    description="Обновление статуса жалобы (используется n8n для автоматизации)"
)
async def update_complaint_status(
        complaint_id: int,
        status_update: ComplaintStatusUpdate,
        service: ComplaintsService = Depends(get_complaints_service)
) -> dict:
    """
    Обновление статуса жалобы.
    Используется n8n workflow для автоматического закрытия обработанных жалоб.
    """
    return await service.update_complaint_status(complaint_id, status_update.status)


@router.get(
    "/automation/recent/{category}",
    response_model=List[ComplaintResponse],
    summary="Получение недавних жалоб по категории для автоматизации",
    description="Специальный endpoint для n8n workflow автоматизации"
)
async def get_recent_complaints_for_automation(
        category: str,
        hours: int = Query(1, description="Количество часов назад", ge=1, le=24),
        service: ComplaintsService = Depends(get_complaints_service)
) -> List[ComplaintResponse]:
    """
    Получение недавних жалоб по категории для n8n автоматизации.

    Используется для:
    - Технические жалобы → отправка в Telegram
    - Жалобы по оплате → запись в Google Sheets
    """
    return await service.get_recent_complaints_for_automation(category, hours)