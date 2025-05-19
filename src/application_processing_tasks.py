import logging
import asyncio

from aiogram import Bot
from typing import Tuple, List, Optional
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

async def create_test_vacancy_task() -> None:
    # [DEV MODE ONLY]
    with Session() as db:
        try:
            vacancy1 = Vacancy(
                title="Оператор контактного центра",
                description="Оператор контактного центра ПЦП ЕРКЦ (г. Екатеринбург)",
                created_at=datetime.now(timezone.utc)
            )

            db.add(vacancy1)
            db.flush()
            
            test_vacancy_id_1 = vacancy1.id
            
            for q_data in QUESTION_DATA:
                question = BotQuestion(
                    vacancy_id = test_vacancy_id_1,
                    question_text = q_data['question_text'] if 'question_text' in q_data else None,
                    order = q_data['order'] if 'order' in q_data else None,
                    expected_format = q_data['expected_format'] if 'expected_format' in q_data else None,
                    choices = q_data['choices'] if 'choices' in q_data else None,
                    is_for_screening = q_data['is_for_screening'] if 'is_for_screening' in q_data else False,
                    screening_criteria = q_data['screening_criteria'] if 'screening_criteria' in q_data else None
                )
                db.add(question)

            db.commit()
        except Exception as e:
            logger.error(f"COULDNT CREATE VACANCY: {str(e)}")
            return
    
    # test_return_data = [
    #     ("https://nizhny-tagil.hh.ru/resume/27597eb2ff0e7799050039ed1f494d63716948", test_vacancy_id_1),
    #     ("https://hh.ru/resume/0343600aff0c1b1b130039ed1f4a7a6e7a494c", test_vacancy_id_1) 
    # ]
    
    # return test_return_data


async def resumes_processing_task(bot: Bot, resumes_data: Optional[List[Tuple[str, int]]],  delay_hours: int = 24) -> None:
    #while True:
        try:
            '''
                TODO:
                - async def fetch_new_resumes_data() - способ получения URL для парсинга:
                вообще весь проект без API HH не работает, так как иначе ссылки на резюме нужно ручками
                кидать HR'у, что как бы хрень какая-то.
            '''
            # Получаем новые ссылки на резюме
            # resumes_data = create_test_vacancy_task()
            if not resumes_data:
                logger.error(f'No resumes_data were provided')
                return
            
            # Парсим информацию по ссылкам на резюме              
            parsed_results = await parse_multiple_resumes(resumes_data=resumes_data)
            
            if all(item is None for item in parsed_results):
                logger.error(f'Resume parsing returned no info. Skipping updates')
                return
            
            # Заполняем базу данных необходимыми сущностями
            created_entries = await create_candidates_entries(bot=bot, resumes=parsed_results)
            if not created_entries:
                logger.error(f'No resume entries were created. Skipping updates')

            for resume_data, resume_id in created_entries:
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
            
        #await asyncio.sleep(3600 * delay_hours)