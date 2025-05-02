from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer, 
    DateTime
)
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from src.database.session import Base
import secrets


class RegistrationToken(Base):
    """
    Модель токена для регистрации HR-специалиста в Telegram боте
    
    Fields:
        token (str): Токен регистрации
        created_by (int): HR-специалист админ, раздавший токен
        used_by (int): Пользователи токена
        expires_at (datetime): Истечение срока действия токена
        used_at (datetime): Время задействования токена
    """
    __tablename__ = 'registration_tokens'
    
    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True)
    created_by = Column(Integer, ForeignKey("hr_specialists.id"))
    used_by = Column(Integer, ForeignKey("hr_specialists.id"), nullable=True)
    expires_at = Column(DateTime)
    used_at = Column(DateTime, nullable=True)
    
    creator = relationship(
        "HrSpecialist",
        foreign_keys=[created_by],
        back_populates="created_tokens"
    )
    used_by_hr = relationship(
        "HrSpecialist",
        foreign_keys=[used_by],
        back_populates="used_tokens"
    )
    
    @classmethod
    def generate_token(cls, creator_id: int, duration_hours: int = 24):
        return cls(
            token=secrets.token_urlsafe(32),
            created_by=creator_id,
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours)
        )
    