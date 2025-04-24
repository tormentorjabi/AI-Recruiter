import logging
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
from sqlalchemy import text
from datetime import datetime

from src.database.session import Session
from src.database.models import (
    Candidate, Application, Vacancy, BotQuestion,
    HrNotification, HrSpecialist
)

from src.database.models.application import ApplicationStatus

from tests.bot_questions_data import QUESTION_DATA

from src.database.utils.generate_application_token import set_application_token

logger = logging.getLogger(__name__)
tests_router = Router()


def generate_random_score():
    while True:
        random_number = random.random() * 100
        if 0 <= random_number <= 100:
            return round(random_number / 100, 2)


@tests_router.message(Command('clr_db'))
async def truncate_database(message: Message):
    try:
        await message.answer(
            "❗️ВНИМАНИЕ❗️\n"
            "ВЫ ВЫПОЛНЯЕТЕ КОМАНДУ ТИПА `[DEVELOPMENT]`\n\n"
            "У ВАС НЕ ДОЛЖНО БЫТЬ ДОСТУПА К НЕЙ В СОСТОЯНИИ `[PRODUCTION]`",
            parse_mode='Markdown'
        )
        with Session() as db:
            await message.answer(
                "❗️ВЫПОЛНЯЕМ ОЧИСТКУ БД...❗️\n"
            )
            
            query = (
            "TRUNCATE applications, candidates, vacancies, "
            "bot_questions, bot_interactions, hr_notifications, hr_specialists CASCADE"
            )
            
            db.execute(text(query))
            db.commit()
            
            await message.answer(
                "❗️ОЧИСТКА БД УСПЕШНА❗️"
            )
        
    except Exception as e:
        logger.error(f'Error in clear_database: {str(e)}')


@tests_router.message(Command('token_test'))
async def populate_database_and_generate_candidate_token_test(message: Message):
    try:
        await truncate_database(message)
        with Session() as db:
            await message.answer(
                "ПРИСТУПАЕМ К ЗАПОЛНЕНИЮ БД..."
            )
            
            # Создаем и записываем в БД тестовую вакансию
            vacancy = Vacancy(
                title = 'Тестовая вакансия',
                description = 'Описание для вакансии',
                created_at = datetime.utcnow()
            )
            # Создаем и записываем в БД тестового кандидата БЕЗ Telegram ID
            candidate = Candidate(
                full_name = "ФАМИЛИЯ ИМЯ ОТЧЕСТВО",
                birth_date = '1991-01-01',
                city = None,
                citizenship = None,
                relocation_ready = True
            )
            
            db.add(vacancy)
            db.add(candidate)
            db.flush()

            # Создаем и записываем в БД вопросы для созданной вакансии
            for q_data in QUESTION_DATA:
                question = BotQuestion(
                    vacancy_id = vacancy.id,
                    question_text = q_data['question_text'],
                    order = q_data['order'],
                    expected_format = q_data['expected_format'],
                    choices = q_data['choices']
                )
                db.add(question)
                
            # Создаем и записываем в БД его отклик
            application = Application(
                candidate_id = candidate.id,
                vacancy_id = vacancy.id,
                status = ApplicationStatus.ACTIVE,
                application_date = datetime.utcnow()
            )
            
            db.add(application)
            db.flush()
            
            application_id = application.id
            is_telegram_id_present = True if candidate.telegram_id else False
            
            db.commit()
            
        await message.answer(
            "🔥 БД ЗАПОЛНЕНА ТЕСТОВЫМИ ДАННЫМИ"
        )
        
        # При парсинге резюме кандидата, мы не нашли у него Telegram ID,
        # поэтому создали отклик без данной информации. Но теперь нам нужно
        # сгенерировать токен для идентификации его в боте и отправить ему, каким-то образом:
        if not is_telegram_id_present:
            returned_token_value = await send_application_token(application_id=application_id)
            await message.answer(
                "Имитация отправки токена кандидату успешна\n\n"
                f"Токен, который был сгенерирован для кандидата: `{returned_token_value}`\n"
                "Теперь можно пройти сценарий для кандидата без TG ID в резюме по команде: /start",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f'Error in populate_database_test: {str(e)}')
        

@tests_router.message(Command('notification_test'))
async def create_notifications(message: Message):
    try:
        args = message.text.split(maxsplit=1)[1:] if len(message.text.split()) > 1 else []
        count = int(args[0].strip())
        with Session() as db:
            await message.answer(
                "ПРИСТУПАЕМ К ЗАПОЛНЕНИЮ БД..."
            )
         
            # Создаем и записываем в БД тестовую вакансию
            vacancy = Vacancy(
                title = 'Тестовая вакансия',
                description = 'Описание для вакансии',
                created_at = datetime.utcnow()
            )
            
            # Создаем и записываем в БД тестового кандидата
            candidate = Candidate(
                full_name = "ФИО_КАНДИДАТА",
                birth_date = '1991-01-01',
                city = None,
                citizenship = None,
                relocation_ready = True,
                telegram_id=str(message.from_user.id)
            )
            
            hr = HrSpecialist(
                telegram_id=str(message.from_user.id),
                full_name="Maxim",
                is_approved=True,
                work_mode=True,
                created_at=datetime.utcnow()
            )
            
            # Создаем и записываем в БД его отклик
            application = Application(
                candidate_id = candidate.id,
                vacancy_id = vacancy.id,
                status = ApplicationStatus.ACTIVE,
                application_date = datetime.utcnow()
            )
            
            db.add(hr)
            db.add(vacancy)
            db.add(candidate)
            db.add(application)
            db.flush()

            for i in range(0, count):
                score = generate_random_score()
                notification = HrNotification(
                    candidate_id=candidate.id,
                    hr_specialist_id=hr.id,
                    vacancy_id=vacancy.id,
                    application_id=application.id,
                    channel='telegram',
                    analysis_score=score,
                    final_decision='approve' if score > 0.8 else 'reject',
                    sent_at=datetime.utcnow(),
                    status='new'
                )
                db.add(notification)
            
            db.commit()    
        await message.answer(
        "🔥 БД ЗАПОЛНЕНА ТЕСТОВЫМИ ДАННЫМИ"
    )
    except Exception as e:
        logger.error(f'Error in create_notifications: {str(e)}')
        
        
async def send_application_token(application_id, candidate_email=None, candidate_phone=None):
    '''Имитация генерации и отправки токена идентификации кандидата для его отклика'''
    token = set_application_token(application_id=application_id)
    if not token:
        logger.error(f'Failed to generate token for application with ID: {application_id}')
        return ''
    
    with Session() as db:
        application = db.query(Application).get(application_id)
        if not application:
            return ''
            
        candidate = db.query(Candidate).get(application.candidate_id)
        if not candidate:
            return ''
        
        if candidate_email:
            # Например отправка по email?
            return ''
        
        elif candidate_phone:
            # Например отправка по телефону?
            return ''
        
        else:
            return token