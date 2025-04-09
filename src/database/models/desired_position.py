from sqlalchemy import (
    Column,
    Integer, 
    String,
    Numeric,
    ForeignKey
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class DesiredPosition(Base):
    """
    Модель желаемых условий труда кандидата
    
    Fields:
        resume_id (int): FK на резюме кандидата
        position (str): Желаемая позиция
        salary (numeric): Желаемая заработная плата
    """
    __tablename__ = 'desired_positions'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    position = Column(String(255))
    salary = Column(Numeric)
    
    resume = relationship("Resume", back_populates="desired_position")
    schedules = relationship("DesiredPositionSchedule", back_populates="desired_position")
    employment_types = relationship("DesiredPositionEmployment", back_populates="desired_position")
    