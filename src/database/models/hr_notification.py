from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Integer, 
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from session import Base


class HrNotification(Base):
    """
    Модель сообщения для HR-специалиста
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        channel (str): Канал связи с HR-специалистом
        sent_data (JSONB): Данные для передачи
        sent_at (datetime): Время отправления сообщения
        status (str): Статус отправки сообщения
    """
    __tablename__ = 'hr_notifications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    channel = Column(String(20), server_default='telegram')
    sent_data = Column(JSONB)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), server_default='sent')
    