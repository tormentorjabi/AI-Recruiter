from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    DateTime
)
from session import Base


class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    vacancy_id = Column(String(50))
    application_date = Column(DateTime)
    