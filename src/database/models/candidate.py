from sqlalchemy import (
    Column,
    Integer, 
    String, 
    Boolean, 
    Date, 
    DateTime
)
from datetime import datetime
from session import Base


class Candidate(Base):
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255))
    birth_date = Column(Date)
    city = Column(String(100))
    citizenship = Column(String(100))
    relocation_ready = Column(Boolean)
    telegram_id = Column(String(50))
    status = Column(String(50), server_default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    