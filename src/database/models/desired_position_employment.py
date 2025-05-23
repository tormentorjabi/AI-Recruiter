from sqlalchemy import (
    Column,
    ForeignKey,
    Integer
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class DesiredPositionEmployment(Base):
    """
    Модель обёртки связи M:M желаемых условий труда к типу занятости
    
    Fields:
        employment_type_id (int): FK на тип занятости
        desired_position_id (int): FK на желаемые условия труда
    """
    __tablename__ = 'desired_position_employment'
    
    id = Column(Integer, primary_key=True)
    employment_type_id = Column(Integer, ForeignKey('employment_types.id'))
    desired_position_id = Column(Integer, ForeignKey('desired_positions.id'))
    
    desired_position = relationship("DesiredPosition", back_populates="employment_types")
    employment_type = relationship("EmploymentType", back_populates="desired_positions")
    