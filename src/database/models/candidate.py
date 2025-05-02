from sqlalchemy import (
    Column,
    Integer, 
    String, 
    Boolean, 
    Date, 
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from datetime import datetime


class Candidate(Base):
    """
    Модель соискателя вакансии
    
    Fields:
        full_name (str): Полное имя
        birth_date (date): Дата рождения
        age (int): Возраст
        city (str): Город проживания
        citizenship (str): Гражданство
        relocation_ready (bool): Готовность к переезду
        telegram_id (str): ID Telegram
        status (str): Статус кандидата
        created_at (datetime): Время создания записи
        updated_at (datetime): Время обновления записи
    """
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=True)
    birth_date = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True)
    citizenship = Column(String(100), nullable=True)
    relocation_ready = Column(Boolean, nullable=True)
    telegram_id = Column(String(50))
    status = Column(String(50), server_default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete")
    notifications = relationship("HrNotification", back_populates="candidate")
    interactions = relationship("BotInteraction", back_populates="candidate")
    analysis_results = relationship("AnalysisResult", back_populates="candidate")
    applications = relationship("Application", back_populates="candidate")
    # Removal's reason: described in CandidateAnswer.py file
    # answers = relationship("CandidateAnswer", back_populates="candidate")
    