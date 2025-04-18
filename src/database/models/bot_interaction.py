from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    Enum,
    DateTime,
    JSON
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from enum import Enum as PyEnum
from datetime import datetime


class InteractionState(PyEnum):
    STARTED = "started"
    ANSWERING = "answering"
    REVIEW = "review"
    COMPLETED = "completed"
    PAUSED = "paused"

class BotInteraction(Base):
    """
    Модель единицы взаимодействия Telegram бота
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        current_question_id (int): FK на текущий вопрос из банка вопросов
        application_id (int): FK на отклик
        vacancy_id (int): FK на вакансию
        current_step (int): Номер текущего шага
        answers (JSON): Промежуточные ответы {question_id: answer_text}\
        state (enum): Статус интерактива
        started_at (datetime): Время начала интерактива
        last_active (datetime): Последнее время интерактива
        completed_at (datetime): Время завершения интерактива
    """
    __tablename__ = 'bot_interactions'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)
    current_question_id = Column(Integer, ForeignKey('bot_questions.id'))
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    current_step = Column(Integer, default=0)
    answers = Column(JSON, default={})
    state = Column(Enum(InteractionState), default=InteractionState.STARTED)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="interactions")
    application = relationship("Application", back_populates="interaction")
    vacancy = relationship("Vacancy")
    current_question = relationship("BotQuestion")
    