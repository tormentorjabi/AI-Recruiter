from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from src.bot.config import TELEGRAM_BOT_TOKEN


storage = MemoryStorage()
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
