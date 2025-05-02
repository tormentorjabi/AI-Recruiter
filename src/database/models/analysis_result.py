from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class AnalysisResult(Base):
    """
    Модель результатов скрининга GigaChat ответов кандидата в Telegram
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        application_id (int): FK на отклик
        gigachat_score (int): Результат анализа от GigaChat
        final_decision (str): Решение по кандидату ('approve' / 'rejected' / 'need_more_info')
        processed_at (datetime): Время обработки запроса
    """
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    application_id = Column(Integer, ForeignKey('applications.id'))
    gigachat_score = Column(Integer)
    final_decision = Column(String(20))
    processed_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="analysis_results")
    application = relationship("Application", back_populates="analysis_results")
    