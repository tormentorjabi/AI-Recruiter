import os
import asyncio
import logging

from aiogram.types import BotCommand
from dotenv import load_dotenv
from src.bot.core.bot import bot, dp
from src.gigachat_module.custom_llm_task import custom_llm_task_loop


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()


async def main() -> None:
    try:
        commands = [
            BotCommand(command='/start', description='Запуск бота'),
            BotCommand(command='/register_hr', description='Регистрация (для HR-специалиста)'),
            BotCommand(command='/change_work_mode', description='Сменить режим работы (для HR-специалиста)'),
            BotCommand(command='/delete_hr', description='Удаление HR-специалиста (для Админа)'),
            BotCommand(command='/generate_token', description='Генерация токена регистрации (для Админа)'),
            BotCommand(command='/list_hr', description='Список зарегистрированых HR-специалистов (для Админа)')
        ]
        
        set_bot_commands = asyncio.create_task(bot.set_my_commands(commands=commands))
        bot_task = asyncio.create_task(dp.start_polling(bot))
        llm_task = asyncio.create_task(custom_llm_task_loop())

        await asyncio.gather(
            set_bot_commands,
            bot_task,
            llm_task
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
