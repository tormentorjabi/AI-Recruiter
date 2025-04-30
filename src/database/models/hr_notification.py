from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Integer, 
    DateTime,
    Float
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from datetime import datetime
from enum import Enum


class NotificationStatus(Enum):
    NEW = "new"
    PROCESSING = "processing"
    APPROVED = "approved"
    DECLINED = "declined"


class HrNotification(Base):
    """
    Модель сообщения для HR-специалиста
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        hr_specialist_id (int): FK на HR-специалиста
        vacancy_id (int): FK на вакансию
        application_id (int): FK на отклик
        channel (str): Канал связи с HR-специалистом
        analysis_score (float): Оценка GigaChat
        final_decision (str): Решение по отклику от GigaChat (approve/reject)
        sent_at (datetime): Время отправления сообщения
        status (str): Статус отработки по кандидату HR'ом
    """
    __tablename__ = 'hr_notifications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    hr_specialist_id = Column(Integer, ForeignKey('hr_specialists.id'), nullable=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    application_id = Column(Integer, ForeignKey('applications.id'))
    channel = Column(String(20), server_default='telegram')
    analysis_score = Column(Float)
    final_decision = Column(String(20))
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), server_default='new')
    
    candidate = relationship("Candidate", back_populates="notifications")
    vacancy = relationship("Vacancy", back_populates="notifications")
    application = relationship("Application", back_populates="notification")
    hr_specialist = relationship("HrSpecialist",
                                 foreign_keys=[hr_specialist_id], 
                                 back_populates="notifications")
    