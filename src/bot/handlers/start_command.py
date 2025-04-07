from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart


start_router = Router()

@start_router.message(CommandStart)
async def welcome_command(message: Message):
    user_commands = (
        "• /register_hr — Зарегистрироваться как HR-специалист\n"
    )
    admin_commands = (
        "Команды администратора:\n"
        "• /generate_token — Сгенерировать токен для регистрации HR\n"
        "• /list_hr — Список зарегистрированных HR-специалистов\n"
        "• /delete_hr <Telegram ID HR-специалиста> — Удалить HR-специалиста\n"
    )
    
    await message.answer(
        "Доступные команды:\n"
        f"{user_commands}\n"
        f"{admin_commands}"
    )
    