from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,  
    Boolean
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class ResumeCriteriaField(Base):
    """
    Модель критерия обработки полей резюме кандидата для скрининга резюме
    
    Fields:
        criteria_id (int): FK на конфигурацию ResumeScreeningCriteria
        resume_field (str): Поле резюме, которое будет обрабатываться скринингов (Навыки, Образование и т.д)
        prompt_template (str): Промпт критерия обработки нейросетью
        weight (int): Вес критерия (по умолчанию = 1)
        is_active (bool): Активность критерия
    """
    __tablename__ = 'resume_criteria_fields'
    
    id = Column(Integer, primary_key=True)
    criteria_id = Column(Integer, ForeignKey('resume_screening_criterias.id'))
    resume_field = Column(String, nullable=False)
    prompt_template = Column(String, nullable=False)
    weight = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    criteria = relationship('ResumeScreeningCriteria', back_populates='fields')
    