from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart


start_router = Router()

@start_router.message(CommandStart)
async def welcome_command(message: Message):
    await message.answer(
        "Доступные команды:\n\n"
        "• /registerHR — Зарегистрироваться как HR-специалист\n"
        "• /generate_token — Сгенерировать токен для регистрации HR (только для администраторов)",
        parse_mode="HTML"
    )
    