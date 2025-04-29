import asyncio
import logging

from aiogram.types import BotCommand
from dotenv import load_dotenv

from src.bot.core.bot import bot, dp
from src.bot.utils.check_abandoned_forms import check_abandoned_forms
from src.gigachat_module.parser import get_multiple_resumes
from src.gigachat_module.utils.resume_processing import resume_processing_task
# [DEV MODE ONLY]
# from src.gigachat_module.custom_llm_task import custom_llm_task_loop


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()


async def main() -> None:
    try:
        commands = [
            # Production commands
            BotCommand(command='/start', description='Запуск бота'),
            BotCommand(command='/cancel', description='Отменить процесс заполнение анкеты (для соискателя по вакансии)'),
            BotCommand(command='/register_hr', description='Регистрация (для HR-специалиста)'),
            BotCommand(command='/get_reviews', description='Посмотреть решения по кандидатам (для HR-специалиста)'),
            # BotCommand(command='/change_work_mode', description='Сменить режим работы (для HR-специалиста)'),
            BotCommand(command='/generate_token', description='Генерация токена регистрации (для Админа)'),
            BotCommand(command='/delete_hr', description='Удаление HR-специалиста (для Админа)'),
            BotCommand(command='/list_hr', description='Список зарегистрированых HR-специалистов (для Админа)'),
             # [DEV MODE ONLY] commands
            BotCommand(command='/clr_db', description='Очистить БД (DEV MODE ONLY)'),
            BotCommand(command='/token_test', description='Тест: Регистрация клиента по токену + анкета (DEV MODE ONLY)'),
            BotCommand(command='/notification_test', description='Тест: Меню с решениями для HR (DEV MODE ONLY)'),
        ]
        
        '''
            Сборка основных корутин приложения:
                - resume_processing: парсинг резюме HH по URL.
                - set_bot_commands: меню всплывающих команд Telegram бота.
                - bot_task: основной цикл работы Telegram бота, запуск получения событий.
                - check_abandoned_forms: проверка брошенных анкет и отправка напоминаний.
                - direct_prompts_to_gigachat: прямое общение с моделью GigaChat [DEV MODE ONLY]
        ''' 
        resume_processing = asyncio.create_task(resume_processing_task(delay_hours=1))
        set_bot_commands = asyncio.create_task(bot.set_my_commands(commands=commands))
        bot_task = asyncio.create_task(dp.start_polling(bot))
        abandoned_forms_checks = asyncio.create_task(check_abandoned_forms(bot=bot, delay_minutes=30))
        # [DEV MODE ONLY]
        # direct_prompts_to_gigachat = asyncio.create_task(custom_llm_task_loop()) 

        await asyncio.gather(
            resume_processing,
            set_bot_commands,
            bot_task,
            abandoned_forms_checks,
            # [DEV MODE ONLY]
            # direct_prompts_to_gigachat
        )
    except Exception as e:
        logger.error(f'Error occured: {e}', exc_info=True)
    finally:
        await bot.session.close()
        logger.info('Bot session closed.')
    
if __name__ == "__main__":
    try:
        print('Power on...')
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Turning off...")
