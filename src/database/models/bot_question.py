from sqlalchemy import (
    Column,
    String,
    Integer, 
    Text
)
from session import Base


class BotQuestion(Base):
    """
    Модель вопроса из банка вопросов для Telegram бота
    
    Fields:
        question_text (text): Текст вопроса
        order (int): Порядок вопроса в сценарии
        expected_format (str): Ожидаемый тип ответа ('text' / 'file' / 'choice')
    """
    __tablename__ = 'bot_questions'
    
    id = Column(Integer, primary_key=True)
    question_text = Column(Text)
    order = Column(Integer)
    expected_format = Column(String(20))
    