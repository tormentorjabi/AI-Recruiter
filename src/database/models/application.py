from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    DateTime,
    Enum
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from src.database.session import Base


class ApplicationStatus(PyEnum):
    ACTIVE = "active"
    REVIEW = "review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Application(Base):
    """
    Модель отклика на вакансию
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        vacancy_id (id): FK на вакансию
        status (enum): Статус заявки ('active', 'accepted', 'rejected')
        application_date (datetime): Дата получения отклика
        auth_token (str): Токен, для идентификации кандидата по отклику в Telegram боте
        token_expiry (datetime): Дата истечения жизни токена
    """
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.ACTIVE)
    application_date = Column(DateTime)
    auth_token = Column(String, nullable=True, unique=True, index=True)
    token_expiry = Column(DateTime, nullable=True)
    
    candidate = relationship("Candidate", back_populates="applications")
    vacancy = relationship("Vacancy", back_populates="applications")
    resume = relationship("Resume", back_populates="application")
    analysis_results = relationship("AnalysisResult", back_populates="application")
    interaction = relationship("BotInteraction", back_populates="application")
    # Removal's reason: described in CandidateAnswer.py file
    # answers = relationship("CandidateAnswer", back_populates="application")
    