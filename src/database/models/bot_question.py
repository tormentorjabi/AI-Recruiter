from sqlalchemy import (
    Column,
    Enum,
    Integer, 
    Text,
    ForeignKey,
    JSON
)
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship
from src.database.session import Base


class AnswerFormat(PyEnum):
    TEXT = "text"
    FILE = "file"
    CHOICE = "choice"
    
class BotQuestion(Base):
    """
    Модель вопроса из банка вопросов для Telegram бота
    
    Fields:
        vacancy_id (int): FK на вакансию
        question_text (text): Текст вопроса
        order (int): Порядок вопроса в сценарии
        expected_format (enum): Ожидаемый тип ответа ('text' / 'file' / 'choice')
        choices (JSON): Варианты ответа при expected_format = 'choice'
    """
    __tablename__ = 'bot_questions'
    
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    question_text = Column(Text)
    order = Column(Integer)
    expected_format = Column(Enum(AnswerFormat), nullable=False)
    choices = Column(JSON, nullable=True)
    
    interactions = relationship("BotInteraction", back_populates="current_question")
    vacancy = relationship("Vacancy", back_populates="questions")
    # Removal's reason: described in CandidateAnswer.py file
    # answers = relationship("CandidateAnswer", back_populates="question")
    