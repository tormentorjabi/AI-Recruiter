from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher

from src.bot.config import TELEGRAM_BOT_TOKEN
from src.bot.handlers.start_command import start_router
from src.bot.handlers.admin_commands import admin_router
from src.bot.handlers.hr_registration import registration_router


memory = MemoryStorage()
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=memory)
dp.include_routers(
    admin_router,
    registration_router,
    start_router
)