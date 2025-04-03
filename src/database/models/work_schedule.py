from sqlalchemy import (
    Column,
    Integer, 
    String
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class WorkSchedule(Base):
    """
    Модель графика работы
    
    Fields:
        schedule (str): График работы (
            'Полный день',
            'Сменный график',
            'Гибкий график',
            'Удаленная работа',
            'Вахтовый метод'
        )
    """
    __tablename__ = 'work_schedules'
    
    id = Column(Integer, primary_key=True)
    schedule = Column(String(50))
    
    desired_positions = relationship("DesiredPositionSchedule", back_populates="schedule")
    