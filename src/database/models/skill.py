from sqlalchemy import (
    Column,
    Integer, 
    String
)
from sqlalchemy.orm import relationship
from src.database.session import Base


class Skill(Base):
    """
    Модель навыка
    
    Fields:
        skill_name (str): Название навыка
    """
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True)
    skill_name = Column(String(100))
    
    candidate_skills = relationship("CandidateSkill", back_populates="skill")
    