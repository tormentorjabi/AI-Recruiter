import logging

from typing import List, Optional
from datetime import datetime, timezone, date


from src.database.session import Session
from src.database.models import (
    Candidate, Application, CandidateSkill, DesiredPosition,
    DesiredPositionEmployment, DesiredPositionSchedule, Education,
    EmploymentType, Resume, Skill, WorkExperience, WorkSchedule
)
from src.database.models.application import ApplicationStatus
from src.database.utils.generate_application_token import set_application_token

from src.gigachat_module.parser import ResumeData


logger = logging.getLogger(__name__)


async def create_candidates_entries(resumes: List[ResumeData | None]):
    try:
        with Session() as db:
            for resume_data in resumes:
                if resume_data is None:
                    continue

                candidate = Candidate(
                    full_name=resume_data.name,
                    birth_date=resume_data.birthdate,
                    age=resume_data.age,
                    city=resume_data.address,
                    citizenship=resume_data.citizenship,
                    relocation_ready=resume_data.ready_to_relocate,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(candidate)
                db.flush()
                candidate_id = candidate.id
            
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

                application_id = application.id
                db.commit()
                # TODO:
                # - После генерации токена, его нужно проверить на успешную
                #   генерацию и отправить кандидату.
                #   send_application_token()
                generated_application_token_value = set_application_token(
                    application_id=application_id
                )
                if not generated_application_token_value:
                    logger.error(
                        f"Generated token for application: {application_id} were None."
                    )
                
                resume = Resume(
                    candidate_id=candidate_id,
                    application_id=application_id,
                    resume_link=resume_data.link,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(resume)
                db.flush()
                resume_id = resume.id
                
                if resume_data.position and resume_data.salary:
                    desired_position = DesiredPosition(
                        resume_id=resume_id,
                        position=resume_data.position,
                        salary=resume_data.salary
                    )
                    db.add(desired_position)
                    db.flush()
                    desired_position_id = desired_position.id
                
                if resume_data.employment:
                    work_schedule = resume_data.employment.work_schedule
                    employment_type = resume_data.employment.employment_type
                    
                    employment_entry = EmploymentType(
                        type=employment_type
                    )
                    work_schedule_entry = WorkSchedule(
                        schedule=work_schedule
                    )
                    db.add(employment_entry)
                    db.add(work_schedule_entry)
                    db.flush()
                    # TODO:
                    # - Переделать, у человека может быть множество различных типов
                    #   и графиков, но они они конечны на HH. Пока просто храним большой строкой
                    employment_id = employment_entry.id
                    schedule_id = work_schedule_entry.id
                  
                if employment_id and desired_position_id:
                    dpe_entry = DesiredPositionEmployment(
                        employment_type_id=employment_id,
                        desired_position_id=desired_position_id
                    )
                    db.add(dpe_entry)
                
                if schedule_id and desired_position_id:
                    dps_entry = DesiredPositionSchedule(
                        schedule_id=schedule_id,
                        desired_position_id=desired_position_id
                    )
                    db.add(dps_entry)
                
                if resume_data.skills:
                    for resume_skill in resume_data.skills:
                        skill_id = await _create_or_match_skill(resume_skill)
                        candidate_skill = CandidateSkill(
                            resume_id=resume_id,
                            skill_id=skill_id,
                            proficiency='НАЧАЛЬНЫЙ'
                        )
                        db.add(candidate_skill)
                
                if resume_data.experiences:
                    work_experiences = [
                        WorkExperience(
                            resume_id=resume_id,
                            company=experience_element.company,
                            position=experience_element.position,
                            description=experience_element.description,
                            start_date=_parse_ym_date(experience_element.period[0]),
                            end_date=_parse_ym_date(experience_element.period[1])
                        )
                        for experience_element in resume_data.experiences
                    ]
                    db.add_all(work_experiences)    
                
                db.commit()
                       
    except Exception as e:
        logger.error(f'Error in create_candidate_entry: {str(e)}')
        return
    
    
async def _create_or_match_skill(
    skill: Optional[str]
) -> int:
    if not skill:
        return
    
    try:
        with Session() as db:
            skill_entry = db.query(Skill).filter(
                Skill.skill_name == skill
            ).first()
            
            if skill_entry:
                return skill_entry.id
            
            new_skill = Skill(skill_name=skill)
            
            db.add(new_skill)
            db.flush()
            db.commit()
            
            return new_skill.id
        
    except Exception as e:
        logger.error(f'Error in _create_or_match_skill: {e}')
        return
    
    
def _parse_ym_date(ym_str: Optional[str]) -> Optional[date]:
    '''Сконвертировать 'YYYY-MM' строку в date объект (устанавливается первый день месяца)'''
    if ym_str:
        converted_date = datetime.strptime(ym_str + "-01", "%Y-%m-%d").date()
        return converted_date
    return None