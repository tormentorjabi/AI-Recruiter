from sqlalchemy import (
    Column,
    Integer, 
    String
)
from session import Base


class Skill(Base):
    """
    Модель навыка
    
    Fields:
        skill_name (str): Название навыка
    """
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True)
    skill_name = Column(String(100))
    