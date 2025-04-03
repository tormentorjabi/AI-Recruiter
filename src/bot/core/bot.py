from aiogram.fsm.storage.memory import MemoryStorage
from src.bot.config import TELEGRAM_BOT_TOKEN
from aiogram import Bot, Dispatcher
from src.bot.handlers.admin_commands import admin_router


memory = MemoryStorage()
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=memory)
dp.include_router(admin_router)