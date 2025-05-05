from sqlalchemy import (
    Column,
    Text,
    Integer, 
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from datetime import datetime, timezone


class Vacancy(Base):
    """
    Модель вакансии
    
    Fields:
        title (str): Название вакансии
        description (text): Описание вакансии
        created_at (datetime): Дата создания записи
    """
    __tablename__ = 'vacancies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    notifications = relationship("HrNotification", back_populates="vacancy")
    applications = relationship("Application", back_populates="vacancy")
    questions = relationship("BotQuestion", back_populates="vacancy")
    