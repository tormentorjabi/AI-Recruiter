from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class BotInteraction(Base):
    """
    Модель взаимодействия Telegram бота
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        question_id (int): FK на текущий вопрос из банка вопросов
        user_id (int): ID кандидата в Telegram
        chat_id (int): ID чата с кандидатов в Telegram
        current_state (str): Текущее состояние диалога
        last_active (datetime): Время последней активности диалога
        updated_at (datetime): Дата последнего обновления записи
    """
    __tablename__ = 'bot_interactions'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    question_id = Column(Integer, ForeignKey('bot_questions.id'))
    user_id = Column(Integer)
    chat_id = Column(Integer)
    current_state = Column(String(50))
    last_active = Column(DateTime)
    updated_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="bot_interactions")
    question = relationship("BotQuestion", back_populates="interactions")
    