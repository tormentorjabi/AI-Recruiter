from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from src.bot.config import ADMIN_CHANNEL_ID


start_router = Router()

USER_COMMANDS = (
        "• /register_hr — Зарегистрироваться как HR-специалист\n"
        "• /change_work_mode — Сменить режим работы\n"
    )
ADMIN_COMMANDS = (
        "• /generate_token — Сгенерировать токен для регистрации HR\n"
        "• /list_hr — Список зарегистрированных HR-специалистов\n"
        "• /delete_hr <Telegram ID HR-специалиста> — Удалить HR-специалиста\n"
        "• /change_work_mode — Сменить режим работы (если вы тоже являетесь HR)\n"
    )


@start_router.message(CommandStart)
async def welcome_command(message: Message):
    if message.chat.id != ADMIN_CHANNEL_ID:
        await message.answer(
            "Доступные команды:\n"
            f"{USER_COMMANDS}"
        )
    else:
        await message.answer(
            "Доступные команды:\n"
            f"{ADMIN_COMMANDS}"
        )
    