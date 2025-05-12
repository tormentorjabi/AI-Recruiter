import logging
import asyncio

from typing import Tuple, List
from datetime import timezone, datetime

from src.gigachat_module.resume_screening import ResumeScreening
from src.gigachat_module.parser import parse_multiple_resumes

from src.database.session import Session
from src.database.models import Vacancy, BotQuestion
from src.database.utils.entry_creation import create_candidates_entries
from src.database.utils.entry_update import update_candidate_entry_resume_score

from tests.bot_questions_data import QUESTION_DATA

logger = logging.getLogger(__name__)
resume_screener = ResumeScreening()

def fetch_new_resumes_data() -> List[Tuple[str, int]]:
    '''
        TODO:
            - Возвращать список URL+вакансия(+ её создание)
    '''
    
    # [DEV MODE ONLY]
    with Session() as db:
        try:
            vacancy1 = Vacancy(
                title="Вакансия #1",
                description="Описание вакансии",
                created_at=datetime.now(timezone.utc)
            )

            db.add(vacancy1)
            db.flush()
            
            test_vacancy_id_1 = vacancy1.id
            
            # for q_data in QUESTION_DATA:
            #     question = BotQuestion(
            #         vacancy_id = test_vacancy_id_1,
            #         question_text = q_data['question_text'],
            #         order = q_data['order'],
            #         expected_format = q_data['expected_format'],
            #         choices = q_data['choices']
            #     )
            #     db.add(question)

            db.commit()
        except Exception as e:
            logger.error(f"COULDNT CREATE VACANCY: {str(e)}")
            return
    
    test_return_data = [
        ("https://nizhny-tagil.hh.ru/resume/27597eb2ff0e7799050039ed1f494d63716948", test_vacancy_id_1),
        ("https://ekaterinburg.hh.ru/resume/0343600aff0c1b1b130039ed1f4a7a6e7a494c", test_vacancy_id_1) 
    ]
    
    return test_return_data


async def resumes_processing_task(delay_hours: int = 24) -> None:
    while True:
        try:
            '''
                TODO:
                - async def fetch_new_resumes_data() - способ получения URL для парсинга:
                вообще весь проект без API HH не работает, так как иначе ссылки на резюме нужно ручками
                кидать HR'у, что как бы хрень какая-то.
            '''
            # Получаем новые ссылки на резюме
            resumes_data = fetch_new_resumes_data()
            # Парсим информацию по ссылкам на резюме              
            parsed_results = await parse_multiple_resumes(resumes_data=resumes_data)
            # Заполняем базу данных необходимыми сущностями
            created_resume_ids = await create_candidates_entries(resumes=parsed_results)
            if not created_resume_ids:
                logger.error(f'No resume IDs were created. Skipping updates')
                return

            for resume_data, resume_id in zip(parsed_results, created_resume_ids):
                try:
                    # Отправляем данные о резюме на скрининг GigaChat
                    resume_screening_score = await resume_screener.screen_resume(resume_data=resume_data)
                    # Обновляем сущности в базе данных
                    await update_candidate_entry_resume_score(
                        resume_id=resume_id, 
                        score=resume_screening_score
                    )
                except Exception as e:
                    logger.error(f'Failed to process resume {resume_data.name}: {str(e)}')
                
        except Exception as e:
            logger.error(f'Error in resume_processing_task: {str(e)}', exc_info=True)
            
        await asyncio.sleep(3600 * delay_hours)