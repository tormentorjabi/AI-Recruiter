from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String
)
from src.database.session import Base


class Education(Base):
    """
    Модель уровня образования кандидата
    
    Fields:
        resume_id (int): FK на резюме кандидата
        institution (str): Название учебного заведения
        degree (str): Уровень образования
        field (str): Направление подготовки
        graduation_year (str): Год окончания обучения
    """
    __tablename__ = 'educations'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    institution = Column(String(255))
    degree = Column(String(100))
    field = Column(String(255))
    graduation_year = Column(Integer)
    