from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    Enum,
    DateTime,
    JSON,
    Boolean
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from enum import Enum as PyEnum
from datetime import datetime, timezone


class InteractionState(PyEnum):
    STARTED = "started"
    ANSWERING = "answering"
    REVIEW = "review"
    COMPLETED = "completed"
    PAUSED = "paused"
    NO_CONSENT = "no_consent"

class BotInteraction(Base):
    """
    Модель единицы взаимодействия Telegram бота
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        current_question_id (int): FK на текущий вопрос из банка вопросов
        application_id (int): FK на отклик
        vacancy_id (int): FK на вакансию
        answers (JSON): Промежуточные ответы {question_id: answer_text}
        state (enum): Статус интерактива
        personal_data_consent (bool): Согласие на обработку персональных данных, в рамках отклика
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
    answers = Column(JSON, default={})
    state = Column(Enum(InteractionState), default=InteractionState.STARTED)
    personal_data_consent = Column(Boolean, nullable=True)
    started_at = Column(DateTime, default=datetime.now(timezone.utc))
    last_active = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="interactions")
    application = relationship("Application", back_populates="interaction")
    vacancy = relationship("Vacancy")
    current_question = relationship("BotQuestion")
    