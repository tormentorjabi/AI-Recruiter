import os
import asyncio
import logging
import signal
import platform

from contextlib import asynccontextmanager
from aiogram.types import BotCommand
from dotenv import load_dotenv

from src.bot.core.bot import bot, dp
from src.bot.utils.check_abandoned_forms import check_abandoned_forms
from src.application_processing_tasks import resumes_processing_task


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)
load_dotenv()


async def shutdown(signal, loop):
    logger.info(f'Received EXIT signal {signal.name}...')
    await bot.session.close()
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    
    logger.info("CANCELLING outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    if loop:
        loop.stop()


@asynccontextmanager
async def lifespan():
    """Cross-platform lifespan management"""
    try:
        if platform.system() != 'Windows':
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig, 
                    lambda s=sig: asyncio.create_task(shutdown(s, loop))
                )
        
        yield
        
    except Exception as e:
        logger.error(f"Lifespan error: {e}")
        raise
    finally:
        logger.info("Lifespan cleanup complete")


async def main() -> None:
    async with lifespan():
        try:
            commands = [
                # Production commands
                BotCommand(command='/start', description='Запуск бота'),
                BotCommand(command='/cancel', description='Отменить процесс заполнение анкеты (для соискателя по вакансии)'),
                BotCommand(command='/get_reviews', description='Открыть панель HR (для HR-специалиста)'),
                BotCommand(command='/register_hr', description='Регистрация (для HR-специалиста)'),
                BotCommand(command='/list_vacancies', description='Просмотр вакансий в системе (для Админа)'),
                BotCommand(command='/generate_token', description='Генерация токена регистрации (для Админа)'),
                BotCommand(command='/delete_hr', description='Удаление HR-специалиста (для Админа)'),
                BotCommand(command='/list_hrs', description='Список зарегистрированых HR-специалистов (для Админа)'),
            ]
            
            if os.getenv('ENVIRONMENT') == 'development':
                commands.extend([
                    # [DEV MODE ONLY] commands
                    BotCommand(command='/clr_db', description='Очистить БД (DEV MODE ONLY)'),
                    BotCommand(command='/vacancies_test', description='Тест: Создание вакансий (DEV MODE ONLY)'),
                    BotCommand(command='/token_test', description='Тест: Регистрация клиента по токену + анкета (DEV MODE ONLY)'),
                    BotCommand(command='/notification_test', description='Тест: Меню с решениями для HR (DEV MODE ONLY)'),
                ])
            
            '''
                Сборка основных корутин приложения:
                    - resume_processing: парсинг резюме HH по URL.
                    - set_bot_commands: меню всплывающих команд Telegram бота.
                    - bot_task: основной цикл работы Telegram бота, запуск получения событий.
                    - check_abandoned_forms: проверка брошенных анкет и отправка напоминаний.
                    - direct_prompts_to_gigachat: прямое общение с моделью GigaChat [DEV MODE ONLY]
            ''' 
            
            tasks = [
                asyncio.create_task(resumes_processing_task(bot=bot, delay_hours=24)),
                asyncio.create_task(bot.set_my_commands(commands=commands)),
                asyncio.create_task(dp.start_polling(bot)),
                asyncio.create_task(check_abandoned_forms(bot=bot, delay_minutes=30)),
            ]
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.critical(f'Fatal error occured: {e}', exc_info=True)
            raise

    
if __name__ == "__main__":
    try:
        logger.info('Application STARTING...')
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Application SHUTDOWN requested')
    except Exception as e:
        logger.critical(f'Unexpected error: {str(e)}', exc_info=True)
