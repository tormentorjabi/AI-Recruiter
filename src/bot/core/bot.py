import os
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram import Bot, Dispatcher

from dotenv import load_dotenv

from src.bot.config import TELEGRAM_BOT_TOKEN

# Основные роутеры
from src.bot.handlers.admin_commands import admin_router
from src.bot.handlers.admin_screening_commands import admin_screening
from src.bot.handlers.hr_registration import hr_registration_router
from src.bot.handlers.hr_commands import hr_commands_router
from src.bot.handlers.candidate_commands import candidate_router

# Тестовые роутеры
from ....tests.tests_commands import tests_router


load_dotenv()

mongo_url = os.environ.get('MONGO_DB_CONNECTION')

memory = MongoStorage.from_url(url=mongo_url)
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=memory)
# Регистрируем роутеры.
# Внимание! 
# Порядок регистрации роутеров имеет значение
if os.getenv('ENVIRONMENT') == 'development':
    dp.include_router(tests_router)
    
dp.include_routers(
    admin_router,
    admin_screening,
    candidate_router,
    hr_registration_router,
    hr_commands_router,
)
