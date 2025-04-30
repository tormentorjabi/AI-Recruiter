import logging
import asyncio

from typing import Tuple, List
from datetime import timezone, datetime

from src.gigachat_module.parser import parse_multiple_resumes, parse_resume
from src.database.utils.entry_creation import create_candidates_entries

from src.database.session import Session
from src.database.models import Vacancy

logger = logging.getLogger(__name__)


def get_resumes_data() -> List[Tuple[str, int]]:
    '''
        TODO:
            - Возвращать список URL+вакансия
    '''
    with Session() as db:
        try:
            vacancy = Vacancy(
                title="Тестовый прогон",
                description="Описание вакансии",
                created_at=datetime.now(timezone.utc)
            )
            db.add(vacancy)
            db.flush()
            
            vacancy_id = vacancy.id
            
            db.commit()
        except Exception as e:
            logger.error(f"COULDNT CREATE VACANCY: {str(e)}")
            return
    
    test_return_data = [
        ("https://nizhny-tagil.hh.ru/resume/27597eb2ff0e7799050039ed1f494d63716948", vacancy_id),
        ("https://ekaterinburg.hh.ru/resume/0343600aff0c1b1b130039ed1f4a7a6e7a494c", vacancy_id) 
    ]
    
    return test_return_data


async def resume_processing_task(delay_hours: int = 24) -> None:
    while True:
        try:
            '''
                TODO:
                    - get_resume_urls() - способ получения URL для парсинга: околонереальная задача имхо,
                        вообще весь проект без API HH не работает, так как иначе ссылки на резюме нужно ручками
                        кидать HR'у, что как бы хрень какая-то.
            '''
            resumes_data = get_resumes_data()              
            parsed_results = await parse_multiple_resumes(resumes_data=resumes_data)
            await create_candidates_entries(resumes=parsed_results)
                
        except Exception as e:
            logger.error(f'Error in resume_processing_task: {str(e)}', exc_info=True)
            
        await asyncio.sleep(3600 * delay_hours)