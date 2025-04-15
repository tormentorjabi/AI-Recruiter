from sqlalchemy import (
    Column,
    Enum,
    Integer, 
    Text,
    ForeignKey
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
    """
    __tablename__ = 'bot_questions'
    
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    question_text = Column(Text)
    order = Column(Integer)
    expected_format = Column(Enum(AnswerFormat), nullable=False)
    
    interactions = relationship("BotInteraction", back_populates="current_question")
    answers = relationship("CandidateAnswer", back_populates="question")
    vacancy = relationship("Vacancy", back_populates="questions")
    