from sqlalchemy import (
    Column,
    String,
    Integer
)
from src.database.session import Base


class EmploymentType(Base):
    """
    Модель типа занятости
    
    Fields:
        type (str): Тип занятости (
            'Полная занятость', 
            'Частичная занятость',
            'Проектная занятость',
            'Волонтёрство',
            'Стажировка'
            )
    """
    __tablename__ = 'employment_types'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    