from sqlalchemy import (
    Column,
    ForeignKey,
    Integer
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class DesiredPositionSchedule(Base):
    """
    Модель обёртки связи M:M желаемых условий труда к графику работы
    
    Fields:
        schedule_id (int): FK на график работы
        desired_position_id (int): FK на желаемые условия труда
    """
    __tablename__ = 'desired_position_schedule'
    
    id = Column(Integer, primary_key=True)
    desired_position_id = Column(Integer, ForeignKey('desired_positions.id'))
    schedule_id = Column(Integer, ForeignKey('work_schedules.id'))
    
    desired_position = relationship("DesiredPosition", back_populates="schedules")
    schedule = relationship("WorkSchedule", back_populates="desired_positions")
    