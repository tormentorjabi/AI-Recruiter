from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String, 
    Text, 
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.database.session import Base
from datetime import datetime


class Resume(Base):
    """
    Модель резюме кандидата
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        application_id (int): FK на отклик
        parsed_text (text): Подготовленные и обобщённые данные резюме, для его отправки в GigaChat
        gigachat_response (JSONB): Последний результат GigaChat по резюме
        analysis_status (str): Текущий статус обработки резюме
        created_at (datetime): Время создания записи
        updated_at (datetime): Время обновления записи
    """
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    application_id = Column(Integer, ForeignKey('applications.id'))
    # В процессе подготовки обработки резюме GigaChat'ом, скорее всего, мы будем
    # конструировать разные данные о кандидате (данные с разных записей в БД)
    # по типу: "Имя+Возраст+Город+Желаемая_зарплата" и т.д.
    # Эту итоговую строку я предлагаю сохранять здесь.
    # Открыто для обсуждения.
    parsed_text = Column(Text)
    gigachat_response = Column(JSONB)
    analysis_status = Column(String(20), server_default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="resumes")
    application = relationship("Application", back_populates="resume")
    desired_position = relationship("DesiredPosition", back_populates="resume")
    work_experiences = relationship("WorkExperience", back_populates="resume")
    educations = relationship("Education", back_populates="resume")
    skills = relationship("CandidateSkill", back_populates="resume")
    