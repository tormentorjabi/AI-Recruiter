import logging
import asyncio

from src.gigachat_module.parser import get_multiple_resumes


logger = logging.getLogger(__name__)


async def resume_processing_task(delay_hours: int = 24) -> None:
    while True:
        try:
            '''
                TODO:
                    - get_resume_urls() - способ получения URL для парсинга: околонереальная задача имхо,
                        вообще весь проект без API HH не работает, так как иначе ссылки на резюме нужно ручками
                        кидать HR'у, что как бы хрень какая-то.
            '''
            url_list = [
                "https://ekaterinburg.hh.ru/resume/0343600aff0c1b1b130039ed1f4a7a6e7a494c",
            ]
            results = await get_multiple_resumes(url_list)
            
            # Заглушка, проверить результати парсинга
            logger.warning(results)
        except Exception as e:
            logger.error(f'Error in resume_processing_task: {str(e)}', exc_info=True)
            
        await asyncio.sleep(3600 * delay_hours)