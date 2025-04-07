from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart


start_router = Router()

@start_router.message(CommandStart)
async def welcome_command(message: Message):
    user_commands = (
        "• /registerHR — Зарегистрироваться как HR-специалист\n"
    )
    admin_commands = (
        "Команды администратора:\n"
        "• /generate_token — Сгенерировать токен для регистрации HR\n"
        "• /list_HR — Список зарегистрированных HR-специалистов"
    )
    
    await message.answer(
        "Доступные команды:\n"
        f"{user_commands}\n"
        f"{admin_commands}",
        parse_mode="HTML"
    )
    