from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String, 
    Boolean
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class ResumeScreeningCriteria(Base):
    """
    Модель конфигурации критериев скрининга резюме для вакансии
    
    Fields:
        vacancy_id (int): FK на вакансию
        name (str): Название конфигурации
        description (str): Описание конфигурации
        is_active (bool): Активность конфигурации
    """
    __tablename__ = 'resume_screening_criterias'
    
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    name = Column(String)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    
    fields = relationship('ResumeCriteriaField', back_populates='criteria')
