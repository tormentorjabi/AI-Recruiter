from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String, 
    Text, 
    DateTime
)
from sqlalchemy.orm import relationship
from src.database.session import Base
from datetime import datetime, timezone


class Resume(Base):
    """
    Модель резюме кандидата
    
    Fields:
        candidate_id (int): FK на соискателя по вакансии
        application_id (int): FK на отклик
        resume_link (text): Ссылка на резюме на HH.ru
        parsed_text (text): Подготовленные и обобщённые данные резюме, для его отправки в GigaChat
        gigachat_score (int): Результат оценки GigaChat по резюме
        analysis_status (str): Текущий статус обработки резюме
        created_at (datetime): Время создания записи
        updated_at (datetime): Время обновления записи
    """
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    application_id = Column(Integer, ForeignKey('applications.id'), unique=True)
    resume_link = Column(Text)
    # UPD 01.05.2025:
    # - Предложение более неактуально, поле не используется. 
    #   Удалено.
    #
    # MSG 31.03.2025:
    # - В процессе подготовки обработки резюме GigaChat'ом, скорее всего, мы будем
    #   конструировать разные данные о кандидате (данные с разных записей в БД)
    #   по типу: "Имя+Возраст+Город+Желаемая_зарплата" и т.д.
    #   Эту итоговую строку я предлагаю сохранять здесь.
    #   Открыто для обсуждения.
    #
    # parsed_text = Column(Text)
    gigachat_score = Column(Integer)
    analysis_status = Column(String(20), server_default='pending')
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="resumes")
    application = relationship("Application", back_populates="resume")
    desired_position = relationship("DesiredPosition", back_populates="resume")
    work_experiences = relationship("WorkExperience", back_populates="resume")
    educations = relationship("Education", back_populates="resume")
    skills = relationship("CandidateSkill", back_populates="resume")
    