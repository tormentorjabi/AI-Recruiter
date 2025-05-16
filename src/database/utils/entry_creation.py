import logging
import os

from aiogram import Bot
from dotenv import load_dotenv
from typing import List, Optional, Any, Tuple
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session as SqlAlchemySession

from src.database.session import Session
from src.database.models import (
    Candidate, Application, CandidateSkill, DesiredPosition,
    DesiredPositionEmployment, DesiredPositionSchedule, Education,
    EmploymentType, Resume, Skill, WorkExperience, WorkSchedule
)
from src.database.models.application import ApplicationStatus
from src.database.utils.generate_application_token import set_application_token

from src.gigachat_module.parser import ResumeData

load_dotenv()
ADMIN_CHANNEL_ID = int(os.environ.get("ADMIN_CHANNEL_ID"))
logger = logging.getLogger(__name__)


async def create_candidates_entries(bot: Bot, resumes: List[Optional[ResumeData]]) -> List[Tuple[ResumeData, int]]:
    '''
    Создать записи в базе данных для списка кандидатов, 
    по данным с резюме и вернуть замапленные (resume_data, id) пары
    
    Args:
        resumes: Список ResumeData (может содержать None значения)
    
    Returns:
        Список кортежей, содержащих (resume_data_info, created_resume_id) для успешно созданных объектов в БД
    '''
    try:
        resume_data_to_ids = []
        with Session() as db:
            for resume_data in filter(None, resumes):
                resume_id = await _process_single_resume(bot, db, resume_data)
                if resume_id:
                    resume_data_to_ids.append((resume_data, resume_id))
            return resume_data_to_ids
    except Exception as e:
        logger.error(f'Error in create_candidate_entry: {str(e)}')
        return []


async def _process_single_resume(bot: Bot, db: SqlAlchemySession, resume_data: ResumeData) -> int:
    '''Процессинг единичного резюме с созданием всех необходимых моделей'''
    candidate = _create_candidate(db, resume_data)
    application = _create_application(db, resume_data, candidate.id)
    # TODO: Переделать
    t = _handle_application_token(db, application.id)

    await bot.send_message(
        chat_id=ADMIN_CHANNEL_ID,
        text=f'*Токен для кандидата - {candidate.full_name}:*\n\n🤖 `{t}`',
        parse_mode="Markdown"
    )
    
    resume = await _create_resume(db, resume_data, candidate.id, application.id)
    if not resume:
        return
    
    resume_id = resume.id
    
    desired_position_id = None
    if resume_data.position and resume_data.salary:
        desired_position_id = _create_desired_position(db, resume_data, resume.id)
    
    employment_id, schedule_id = _handle_employment_data(
        db, 
        resume_data, 
        desired_position_id
    )
    
    if resume_data.skills:
        await _process_skills(db, resume_data.skills, resume.id)
    
    if resume_data.experiences:
        _process_experiences(db, resume_data.experiences, resume.id)
    
    db.commit()
    return resume_id


def _create_candidate(db: SqlAlchemySession, resume_data: ResumeData) -> Candidate:
    '''Создание и наполнение Candidate модели'''
    now = datetime.now(timezone.utc)
    candidate = Candidate(
        full_name=resume_data.name,
        birth_date=resume_data.birthdate,
        age=resume_data.age,
        city=resume_data.address,
        citizenship=resume_data.citizenship,
        relocation_ready=resume_data.ready_to_relocate,
        created_at=now,
        updated_at=now
    )
    db.add(candidate)
    db.flush()
    return candidate


def _create_application(db: SqlAlchemySession, resume_data: ResumeData, candidate_id: int) -> Application:
    '''Создание и наполнение Application модели'''
    application = Application(
        candidate_id=candidate_id,
        vacancy_id=resume_data.vacancy_id,
        status=ApplicationStatus.ACTIVE,
        # Не самое важное поле, но можно более точно
        # отметить временные из данных отклика (только с API HH)            
        application_date=datetime.now(timezone.utc)
    )
    db.add(application)
    db.flush()
    return application


def _handle_application_token(db: SqlAlchemySession, application_id: int) -> str:
    '''Генерация и установка токена идентификации кандидата'''
    # TODO:
    # - После генерации токена, его нужно проверить на успешную
    #   генерацию и отправить кандидату.
    #   send_application_token()
    generated_token = set_application_token(db, application_id)
    if not generated_token:
        logger.error(f"Generated token for application: {application_id} was None.")
        return None
    return generated_token


async def _create_resume(db: SqlAlchemySession, resume_data: ResumeData, candidate_id: int, application_id: int) -> Resume:
    '''Создание и наполнение Resume модели'''
    try:
        existing_resume = db.query(Resume).join(Application).filter(
            Resume.resume_link == resume_data.link,
            Application.vacancy_id == resume_data.vacancy_id
        ).first()
        
        if existing_resume:
            logger.info(f"Duplicate resume found for candidate {candidate_id}, vacancy {resume_data.vacancy_id}")
            return None
        resume_entry = db.query(Resume).filter_by(
            resume_link=resume_data.link
        ).first()
    except Exception as e:
        logger.error(f'Error checking for duplicate resume: {str(e)}')
        return None
    
    try:
        now = datetime.now(timezone.utc)
        resume = Resume(
            candidate_id=candidate_id,
            application_id=application_id,
            resume_link=resume_data.link,
            created_at=now,
            updated_at=now
        )
        db.add(resume)
        db.flush()
        return resume
    except Exception as e:
        logger.error(f'Error creating resume: {str(e)}')
        db.rollback()
        return None


def _create_desired_position(db: SqlAlchemySession, resume_data: ResumeData, resume_id: int) -> int:
    '''Создание и наполнение DesiredPosition модели'''
    desired_position = DesiredPosition(
        resume_id=resume_id,
        position=resume_data.position,
        salary=resume_data.salary
    )
    db.add(desired_position)
    db.flush()
    return desired_position.id


def _handle_employment_data(
    db: SqlAlchemySession, 
    resume_data: ResumeData, 
    desired_position_id: Optional[int]
) -> tuple[Optional[int], Optional[int]]:
    '''
        Создание и наполнение EmploymentType и WorkSchedule моделей 
        и разрешение M:M связей с DesiredPosition моделью
    '''
    employment_id = schedule_id = None
    
    if resume_data.employment:
        employment_entry = EmploymentType(type=resume_data.employment.employment_type)
        work_schedule_entry = WorkSchedule(schedule=resume_data.employment.work_schedule)
        
        db.add(employment_entry)
        db.add(work_schedule_entry)
        db.flush()
        
        employment_id = employment_entry.id
        schedule_id = work_schedule_entry.id
        
        if desired_position_id:
            if employment_id:
                db.add(DesiredPositionEmployment(
                    employment_type_id=employment_id,
                    desired_position_id=desired_position_id
                ))
            if schedule_id:
                db.add(DesiredPositionSchedule(
                    schedule_id=schedule_id,
                    desired_position_id=desired_position_id
                ))
    
    return employment_id, schedule_id


async def _process_skills(db: SqlAlchemySession, skills: List[str], resume_id: int) -> None:
    '''Создание и наполнение CandidateSkills модели'''
    for skill in skills:
        skill_id = await _create_or_match_skill(db, skill)
        if skill_id:
            db.add(CandidateSkill(
                resume_id=resume_id,
                skill_id=skill_id,
                proficiency='НАЧАЛЬНЫЙ'
            ))


def _process_experiences(db: SqlAlchemySession, experiences: List[Any], resume_id: int) -> None:
    '''Создание и наполнение WorkExperience модели'''
    work_experiences = [
        WorkExperience(
            resume_id=resume_id,
            company=exp.company,
            position=exp.position,
            description=exp.description,
            start_date=_parse_ym_date(exp.period[0]),
            end_date=_parse_ym_date(exp.period[1])
        )
        for exp in experiences
    ]
    db.add_all(work_experiences)


async def _create_or_match_skill(db: SqlAlchemySession, skill: Optional[str]) -> Optional[int]:
    '''Найти существующий Skill в базе данных или создать новый вид'''
    if not skill:
        return None
    
    try:
        skill_entry = db.query(Skill).filter(Skill.skill_name == skill).first()
        
        if skill_entry:
            return skill_entry.id
        
        new_skill = Skill(skill_name=skill)
        db.add(new_skill)
        db.flush()
        return new_skill.id
        
    except Exception as e:
        logger.error(f'Error in _create_or_match_skill: {e}')
        return None


def _parse_ym_date(ym_str: Optional[str]) -> Optional[date]:
    '''Сконвертировать 'YYYY-MM' строку в date объект (устанавливается первый день месяца)'''
    if not ym_str:
        return None
    return datetime.strptime(ym_str + "-01", "%Y-%m-%d").date()