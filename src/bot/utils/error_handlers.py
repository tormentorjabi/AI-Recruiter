import logging
from aiogram.types import Message


logger = logging.getLogger(__name__)

async def handle_db_error(message: Message, error_msg: str = "Произошла ошибка"):
    '''Лог ошибок, возникающих в результате ошибок БД'''
    await message.answer(f"⚠️ {error_msg}. Попробуйте позже.")
    logger.error(error_msg)