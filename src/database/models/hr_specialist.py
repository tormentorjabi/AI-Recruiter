from sqlalchemy import (
    Column,
    Boolean,
    Integer, 
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from datetime import datetime


class HrSpecialist(Base):
    """
    Модель HR-специалиста
    
    Fields:
        telegram_id (str): ID HR-специалиста в Telegram
        full_name (sdr): ФИО HR-специалиста
        is_approved (boolean): Статус подтверждения профиля в Telegram
        created_at (datetime): Время создания записи
    """
    __tablename__ = 'hr_specialists'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(255))
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    created_tokens = relationship(
        "RegistrationToken",
        foreign_keys="RegistrationToken.created_by",
        back_populates="creator"
    )
    used_tokens = relationship(
        "RegistrationToken",
        foreign_keys="RegistrationToken.used_by",
        back_populates="used_by_hr"
    )
    notifications = relationship("HrNotification", back_populates="hr_specialist")
    