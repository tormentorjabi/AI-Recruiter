from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher

from src.bot.config import TELEGRAM_BOT_TOKEN

# Основные роутеры
from src.bot.handlers.start_command import start_router
from src.bot.handlers.admin_commands import admin_router
from src.bot.handlers.hr_registration import hr_registration_router
from src.bot.handlers.hr_commands import hr_commands_router
from src.bot.handlers.candidate_commands import candidate_router

# Тестовые роутеры
from tests.tests_commands import tests_router


memory = MemoryStorage()
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=memory)
# Регистрируем роутеры.
# Внимание! 
# Порядок регистрации роутеров имеет значение
dp.include_routers(
    admin_router,
    tests_router,
    candidate_router,
    hr_registration_router,
    hr_commands_router,
    #start_router
)