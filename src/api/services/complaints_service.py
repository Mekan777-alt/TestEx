import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from starlette import status as starlette_status
from fastapi import Depends, Request, HTTPException, status

from api.repositories.complaints_repository import ComplaintsRepository, get_complaints_repository
from api.dto.complaints_dto import ComplaintCreate, ComplaintResponse, ComplaintList, ComplaintResponseWorkflow
from models.complaint_model import Complaint
from api.services.sentiment_service import SentimentService, get_sentiment_service
from api.services.spam_service import SpamService, get_spam_service
from api.services.ai_service import AIService, get_ai_service

logger = logging.getLogger(__name__)


class ComplaintsService:
    """Сервис для обработки жалоб"""

    def __init__(
            self,
            complaints_repository: ComplaintsRepository,
            sentiment_service: SentimentService,
            spam_service: SpamService,
            ai_service: AIService
    ):
        self.complaints_repository = complaints_repository
        self.sentiment_service = sentiment_service
        self.spam_service = spam_service
        self.ai_service = ai_service

    async def create_complaint_service(
            self,
            complaint_data: ComplaintCreate,
            request: Request
    ) -> ComplaintResponse:
        """Создание новой жалобы с полной обработкой"""
        try:
            # Получаем данные из middleware
            client_location = getattr(request.state, 'client_location', None)

            # Создаем объект жалобы
            complaint = Complaint(
                text=complaint_data.text,
                status="open",
                timestamp=datetime.utcnow(),
                ip_location=client_location
            )

            # Анализ тональности
            try:
                sentiment = await self.sentiment_service.analyze_sentiment(complaint_data.text)
                complaint.sentiment = sentiment
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
                complaint.sentiment = "unknown"

            # Определение категории
            try:
                category = await self.ai_service.categorize_complaint(complaint_data.text)
                complaint.category = category
            except Exception as e:
                logger.error(f"Ошибка при определении категории: {e}")
                complaint.category = "другое"

            try:
                is_spam = await self.spam_service.check_spam(complaint_data.text)
                complaint.is_spam = is_spam
            except Exception as e:
                logger.error(f"Spam check failed: {e}")
                complaint.is_spam = False

            saved_complaint = await self.complaints_repository.create_complaint(complaint)

            # Запускаем категоризацию асинхронно
            asyncio.create_task(
                self._classification_spam(saved_complaint.id, complaint_data.text)
            )

            return ComplaintResponse(
                id=saved_complaint.id,
                status=saved_complaint.status,
                sentiment=saved_complaint.sentiment,
                category=saved_complaint.category,
            )

        except Exception as e:
            logger.error(f"Error creating complaint: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error while processing complaint"
            )

    async def _classification_spam(self, complaint_id: int, complaint_text: str):
        try:
            is_spam = await self.spam_service.check_spam(complaint_text)
            success = await self.complaints_repository.update_complaint_spam(complaint_id, is_spam)

            if success:
                logger.info(f"Complaint {complaint_id} spam as: {is_spam}")
            else:
                logger.error(f"Failed to update spam for complaint {complaint_id}")
        except Exception as e:
            logger.error(f"{complaint_id}: {e}")

    async def get_complaints_list(
            self,
            status: Optional[str] = None,
            since_hours: Optional[int] = None,
            category: Optional[str] = None,
            sentiment: Optional[str] = None,
            limit: int = 20,
            offset: int = 0
    ) -> ComplaintList:
        try:
            complaints = await self.complaints_repository.get_complaints_with_filters(
                status=status,
                since_hours=since_hours,
                category=category,
                sentiment=sentiment,
                limit=limit,
                offset=offset
            )

            total = await self.complaints_repository.count_complaints_with_filters(
                status=status,
                since_hours=since_hours,
                category=category,
                sentiment=sentiment
            )

            complaint_responses = [
                ComplaintResponseWorkflow(
                    id=complaint.id,
                    status=complaint.status,
                    sentiment=complaint.sentiment,
                    category=complaint.category,
                    timestamp=complaint.timestamp,
                    text=complaint.text,
                    is_spam=complaint.is_spam,
                    ip_location=complaint.ip_location
                )
                for complaint in complaints
            ]

            page = (offset // limit) + 1

            return ComplaintList(
                complaints=complaint_responses,
                total=total,
                page=page,
                per_page=limit
            )

        except Exception as e:
            logger.error(f"Error fetching complaints: {e}")
            raise HTTPException(
                status_code=starlette_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error while fetching complaints"
            )

    async def get_complaint_by_id(self, complaint_id: int) -> ComplaintResponse:
        try:
            complaint = await self.complaints_repository.get_complaint_by_id(complaint_id)

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            return ComplaintResponseWorkflow(
                id=complaint.id,
                status=complaint.status,
                sentiment=complaint.sentiment,
                category=complaint.category,
                timestamp=complaint.timestamp,
                text=complaint.text,
                is_spam=complaint.is_spam,
                ip_location=complaint.ip_location
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching complaint {complaint_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error while fetching complaint"
            )

    async def update_complaint_status(self, complaint_id: int, new_status: str) -> dict:
        try:
            if new_status not in ["open", "closed"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Status must be 'open' or 'closed'"
                )

            success = await self.complaints_repository.update_complaint_status(
                complaint_id, new_status
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            return {"message": f"Complaint {complaint_id} status updated to {new_status}"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating complaint status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error while updating complaint status"
            )

    async def get_recent_complaints_for_automation(
            self,
            category: str,
            hours: int = 1
    ) -> List[ComplaintResponse]:
        """Получение недавних жалоб для автоматизации n8n"""
        try:
            complaints = await self.complaints_repository.get_recent_complaints_by_category(
                category, hours
            )

            return [
                ComplaintResponseWorkflow(
                    id=complaint.id,
                    status=complaint.status,
                    sentiment=complaint.sentiment,
                    category=complaint.category,
                    timestamp=complaint.timestamp,
                    text=complaint.text,
                    is_spam=complaint.is_spam,
                    ip_location=complaint.ip_location
                )
                for complaint in complaints
            ]

        except Exception as e:
            logger.error(f"Error fetching recent complaints: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching recent complaints"
            )



def get_complaints_service(
        complaints_repository: ComplaintsRepository = Depends(get_complaints_repository),
        sentiment_service: SentimentService = Depends(get_sentiment_service),
        spam_service: SpamService = Depends(get_spam_service),
        ai_service: AIService = Depends(get_ai_service)
) -> ComplaintsService:
    return ComplaintsService(
        complaints_repository,
        sentiment_service,
        spam_service,
        ai_service
    )