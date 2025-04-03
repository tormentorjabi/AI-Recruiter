from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.database.session import Base


class AnalysisResult(Base):
    """
    Модель результата анализа кандидата
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        summary (JSONB): Результат анализа от GigaChat
        source (str): Источник оценки (по резюме / по ответам в Telegram)
        final_decision (str): Решение по кандидату ('approve' / 'rejected' / 'need_more_info')
        processed_at (datetime): Время обработки запроса
    """
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    summary = Column(JSONB)
    source = Column(String(20))
    final_decision = Column(String(20))
    processed_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="analysis_results")
    