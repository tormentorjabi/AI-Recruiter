import logging
import src.bot.utils.message_templates as msg_templates

from typing import List
from sqlalchemy import desc
from aiogram import F
from aiogram import Router
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.session import Session
from src.database.models import (
    RegistrationToken, HrSpecialist, Vacancy,
    Application, BotQuestion
)
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID
from src.bot.utils.error_handlers import handle_db_error


logger = logging.getLogger(__name__)
admin_screening = Router()


#---------------
# Display Utilites
#---------------
def _build_vacancies_keyboard(vacancies: List[Vacancy], page: int = 0, items_per_page: int = 10):
    total_pages = (len(vacancies) + items_per_page - 1) // items_per_page
    page_vacancies = vacancies[page*items_per_page:(page+1)*items_per_page]
    
    keyboard = []
    for vacancy in page_vacancies:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📄 {vacancy.title}",
                callback_data=f"vacancy_detail_{vacancy.id}"
            )
        ])
        
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(
                text="◀️", 
                callback_data=f"vacancies_page_{page-1}"
            ))
        pagination.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", 
            callback_data="noop"
        ))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(
                text="▶️", 
                callback_data=f"vacancies_page_{page+1}"
            ))
        keyboard.append(pagination)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@admin_screening.callback_query(F.data.startswith("vacancies_page_"))
async def _handle_vacancies_pagination(callback: CallbackQuery):
    try:
        page = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).all()
            
            await callback.message.edit_reply_markup(
                reply_markup=_build_vacancies_keyboard(vacancies, page=page)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error in vacancies pagination: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Main Commands Handlers
#---------------
@admin_screening.message(
    Command('list_vacancies'),
    F.chat.id == ADMIN_CHANNEL_ID,
    F.from_user.id == ADMIN_USER_ID
)
async def _list_vacancies(message: Message):
    try:
        with Session() as db:
            vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).all()
            
            if not vacancies:
                await message.answer('В системе нет вакансий')
                return
            
            await message.answer(
                "Список вакансий:",
                reply_markup=_build_vacancies_keyboard(vacancies)
            )
    except Exception as e:
        logger.error(f'Error while trying to list vacancies: {str(e)}')
        handle_db_error(message)
        
        
#---------------
# Callback Handlers
#---------------
@admin_screening.callback_query(F.data.startswith("vacancy_params_"))
async def _show_vacancy_params(callback: CallbackQuery):
    try:
        vacancy_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancy = db.query(Vacancy).get(vacancy_id)
            if not vacancy:
                await callback.message.answer("Вакансия не найдена")
                return
            
            questions: List[BotQuestion] = vacancy.questions
            if not questions:
                await callback.message.answer("У данной вакансии нет вопросов")
                return
            
            question_texts = ""
            for question in questions:
                if question.is_for_screening:
                    question_texts += f'*Q{question.order}:* {question.question_text}\n'
                    question_texts += f'*Промпт:* {question.screening_criteria}\n\n'
                else:
                    question_texts += f'*Q{question.order}:* {question.question_text}\n\n'
            
            await callback.message.answer(
                f'*Вопросы:*\n\n{question_texts}',
                parse_mode="Markdown"
            )
            await callback.answer()
    except Exception as e:
        logger.error(f'Error showing vacancy params details: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(F.data.startswith("vacancy_detail_"))
async def _show_vacancy_detail(callback: CallbackQuery):
    try:
        vacancy_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancy = db.query(Vacancy).get(vacancy_id)
            if not vacancy:
                await callback.answer("Вакансия не найдена")
                return
            
            application_count = db.query(Application).filter_by(
                vacancy_id=vacancy_id
            ).count()
            
            detail_text = (
                f"📌 Вакансия: {vacancy.title}\n\n"
                f"🆔 ID: {vacancy.id}\n"
                f"📝 Описание: {vacancy.description}\n"
                f"📅 Создана: {vacancy.created_at.strftime('%Y-%m-%d')}\n"
                f"📅 Откликов: {application_count}\n"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔙 Просмотреть параметры вакансии",
                    callback_data=f"vacancy_params_{vacancy_id}"
                )],
                
                [InlineKeyboardButton(
                    text="🔙 Редактировать параметры вакансии",
                    callback_data=f"edit_vacancy_params_{vacancy_id}"
                )],

                [InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data="back_to_vacancies_list"
                )]
            ])
            
            await callback.message.edit_text(
                detail_text,
                reply_markup=keyboard
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error showing vacancy detail: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(F.data == "back_to_vacancies_list")
async def _back_to_vacancies_list(callback: CallbackQuery):
    try:
        with Session() as db:
            vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).all()
            
            await callback.message.edit_text(
                "📋 Список вакансий в системе:",
                reply_markup=_build_vacancies_keyboard(vacancies)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error returning to vacancies list: {str(e)}')
        await handle_db_error(callback.message)
        

#---------------
# NOOP Handler
#---------------
     
@admin_screening.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    '''
        Пустая операция
        Используется для CallbackQuery которые не требуют обработки
        Например: кнопка с текущей страницей в меню пагинации
    '''
    await callback.answer()