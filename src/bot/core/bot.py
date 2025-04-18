from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher

from src.bot.config import TELEGRAM_BOT_TOKEN
from src.bot.handlers.start_command import start_router
from src.bot.handlers.admin_commands import admin_router
from src.bot.handlers.hr_registration import registration_router
from src.bot.handlers.hr_commands import hr_commands_router
from src.bot.handlers.candidate_commands import candidate_router


memory = MemoryStorage()
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=memory)
dp.include_routers(
    admin_router,
    candidate_router,
    registration_router,
    hr_commands_router,
    start_router
)