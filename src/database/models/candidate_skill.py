from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String
)
from src.database.session import Base


class CandidateSkill(Base):
    """
    Модель навыков кандидата из его резюме
    
    Fields:
        resume_id (int): FK на резюме кандидата
        skill_id (int): FK на навык
        proficiency (str): Уровень владения навыком
    """
    __tablename__ = 'candidate_skills'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    skill_id = Column(Integer, ForeignKey('skills.id'))
    proficiency = Column(String(30))
    