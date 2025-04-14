from sqlalchemy import (
    Column,
    String,
    Integer, 
    Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class BotQuestion(Base):
    """
    Модель вопроса из банка вопросов для Telegram бота
    
    Fields:
        vacancy_id (int): FK на вакансию
        question_text (text): Текст вопроса
        order (int): Порядок вопроса в сценарии
        expected_format (str): Ожидаемый тип ответа ('text' / 'file' / 'choice')
    """
    __tablename__ = 'bot_questions'
    
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    question_text = Column(Text)
    order = Column(Integer)
    expected_format = Column(String(20))
    
    interactions = relationship("BotInteraction", back_populates="question")
    answers = relationship("CandidateAnswer", back_populates="question")
    vacancy = relationship("Vacancy", back_populates="questions")
    