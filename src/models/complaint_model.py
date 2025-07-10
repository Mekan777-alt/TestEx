from datetime import datetime

from sqlalchemy import Integer, Column, Enum, Text, String, DateTime, Boolean
from src.database.base import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    status = Column(Enum("open", "closed"), default="open")
    timestamp = Column(DateTime, default=datetime.utcnow)
    sentiment = Column(String(20), comment="positive/negative/neutral/unknown")
    category = Column(String(20), default="другое", comment="техническая/оплата/другое")

    is_spam = Column(Boolean)
    ip_location = Column(String(100))
