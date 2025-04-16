import os
import asyncio
import logging

from aiogram.types import BotCommand
from dotenv import load_dotenv
from src.bot.core.bot import bot, dp
from src.gigachat_module.client import get_gigachat_client
from langchain_core.messages import HumanMessage, SystemMessage


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def custom_llm_task(prompt: str) -> str:
    """
    Прямое общение с GigaChat, предполагается только для этапа разработки
    
    Args:
        prompt (str): Промпт для отправки в модель
        
    Returns:
        str: Ответ GigaChat
    """
    try:
        giga = get_gigachat_client()
        
        messages = [
            HumanMessage(content=prompt)
        ]
        
        response = giga.invoke(messages)
        return response.content
    
    except Exception as e:
        print(f'Error occured in direct LLM task: {e}')
        return None
    

async def custom_llm_task_loop():
    while True:
        user_input = await asyncio.to_thread(input, "ПРОМПТ ПОЛЬЗОВАТЕЛЯ: ")
        if user_input.strip().upper() == "СТОП":
            break
        response = await asyncio.to_thread(custom_llm_task, user_input)
        print(f"GigaChat ответ: {response}")


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
