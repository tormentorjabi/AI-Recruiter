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
        vacancy_id (str): ID вакансии
        application_date (datetime): Дата получения отклика
    """
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    vacancy_id = Column(String(50))
    application_date = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="applications")
    