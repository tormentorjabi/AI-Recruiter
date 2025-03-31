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
    """
    Модель соискателя вакансии
    
    Fields:
        full_name (str): Полное имя
        birth_date (date): Дата рождения
        city (str): Город проживания
        citizenship (str): Гражданство
        relocation_ready (bool): Готовность к переезду
        telegram_id (str): ID Telegram
        status (str): Статус кандидата
        created_at (datetime): Время создания записи
        updated_at (datetime): Время обновления записи
    """
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
    