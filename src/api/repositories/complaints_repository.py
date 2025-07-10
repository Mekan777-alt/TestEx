from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from database.session import get_session
from models.complaint_model import Complaint


class ComplaintsRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_complaint(self, complaint: Complaint) -> Complaint:
        """Создание новой жалобы"""
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_complaint_by_id(self, complaint_id: int) -> Optional[Complaint]:
        """Получение жалобы по ID"""
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def update_complaint_status(self, complaint_id: int, status: str) -> bool:
        """Обновление статуса жалобы"""
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        complaint = result.scalar_one_or_none()

        if complaint:
            complaint.status = status
            await self.session.commit()
            return True
        return False


    async def update_complaint_spam(self, complaint_id: int, spam: bool) -> bool:
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )

        complaint = result.scalar_one_or_none()

        if complaint:
            complaint.spam = spam
            await self.session.commit()
            return True
        return False

    async def get_complaints_with_filters(
            self,
            status: Optional[str] = None,
            since_hours: Optional[int] = None,
            category: Optional[str] = None,
            sentiment: Optional[str] = None,
            limit: int = 20,
            offset: int = 0
    ) -> List[Complaint]:
        """Получение жалоб с фильтрацией"""
        query = select(Complaint)

        # Применяем фильтры
        conditions = []

        if status:
            conditions.append(Complaint.status == status)

        if since_hours:
            since_time = datetime.utcnow() - timedelta(hours=since_hours)
            conditions.append(Complaint.timestamp >= since_time)

        if category:
            conditions.append(Complaint.category == category)

        if sentiment:
            conditions.append(Complaint.sentiment == sentiment)

        if conditions:
            query = query.where(and_(*conditions))

        # Сортировка и пагинация
        query = query.order_by(Complaint.timestamp.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_complaints_with_filters(
            self,
            status: Optional[str] = None,
            since_hours: Optional[int] = None,
            category: Optional[str] = None,
            sentiment: Optional[str] = None
    ) -> int:
        """Подсчет жалоб с фильтрацией"""
        from sqlalchemy import func

        query = select(func.count(Complaint.id))

        conditions = []

        if status:
            conditions.append(Complaint.status == status)

        if since_hours:
            since_time = datetime.utcnow() - timedelta(hours=since_hours)
            conditions.append(Complaint.timestamp >= since_time)

        if category:
            conditions.append(Complaint.category == category)

        if sentiment:
            conditions.append(Complaint.sentiment == sentiment)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar()

    async def get_recent_complaints_by_category(self, category: str, hours: int = 1) -> List[Complaint]:
        """Получение недавних жалоб по категории (для n8n)"""
        since_time = datetime.utcnow() - timedelta(hours=hours)

        query = select(Complaint).where(
            and_(
                Complaint.category == category,
                Complaint.status == "open",
                Complaint.timestamp >= since_time
            )
        ).order_by(Complaint.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()


def get_complaints_repository(session: AsyncSession = Depends(get_session)):
    return ComplaintsRepository(session)