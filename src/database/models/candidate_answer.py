from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    Text,
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from session import Base


class CandidateAnswer(Base):
    """
    Модель ответов кандидата в Telegram боте
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        question_id (int): FK на текущий вопрос из банка вопросов
        answer_text (text): Подготовленные и обобщенные ответы кандидата, для их отправки в GigaChat
        gigachat_response (JSONB): Последний результат GigaChat по ответам из Telegram бота
        created_at (datetime): Дата создания записи
        updated_at (datetime): Время обновления записи
    """
    __tablename__ = 'candidate_answers'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    question_id = Column(Integer, ForeignKey('bot_questions.id'))
    # Аналогично с resumes.parsed_text предлагаю сохранять здесь итоговую строку,
    # сконструированную из ответов кандидата, которую будем отправлять на обработку
    # в GigaChat
    # Открыто для обсуждения.
    answer_text = Column(Text)
    gigachat_response = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    