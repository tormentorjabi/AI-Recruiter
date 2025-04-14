from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class Application(Base):
    """
    Модель отклика на вакансию
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        vacancy_id (id): FK на вакансию
        status (str): Статус заявки ('pending', 'active', 'completed', 'rejected')
        application_date (datetime): Дата получения отклика
    """
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    status = Column(String(20), default='pending')
    application_date = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="applications")
    vacancy = relationship("Vacancy", back_populates="applications")
    answers = relationship("CandidateAnswer", back_populates="application")
    resume = relationship("Resume", back_populates="application")
    analysis_results = relationship("AnalysisResult", back_populates="application")
    