from sqlalchemy import (
    Column,
    ForeignKey,
    Integer, 
    String,
    Text,
    Date
)
from src.database.session import Base


class WorkExperience(Base):
    """
    Модель опыта работы кандидата
    
    Fields:
        resume_id (int): FK на резюме кандидата
        company (str): Наименование организации
        position (str): Должность
        description (text): Описание должностных обязанностей
        start_date (date): Дата приема на работу
        end_date (date): Дата увольнения с работы
    """
    __tablename__ = 'work_experiences'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    company = Column(String(255))
    position = Column(String(255))
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    