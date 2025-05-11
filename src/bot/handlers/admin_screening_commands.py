import logging
import src.bot.utils.message_templates as msg_templates

from typing import List, Union
from sqlalchemy import desc
from aiogram import F
from aiogram import Router
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from src.database.session import Session
from src.database.models import (Vacancy, Application, BotQuestion)
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID
from src.bot.utils.error_handlers import handle_db_error


logger = logging.getLogger(__name__)
admin_screening = Router()


class QuestionEditingStates(StatesGroup):
    waiting_for_new_text = State()
    waiting_for_screening_criteria = State()
    confirming_delete = State()


#---------------
# Display Utilites
#---------------
def _build_questions_keyboard(questions: List[BotQuestion], vacancy_id: int, page: int = 0, items_per_page: int = 10):
    total_pages = (len(questions) + items_per_page - 1) // items_per_page
    page_questions = questions[page*items_per_page:(page+1)*items_per_page]
    
    keyboard = []
    for question in page_questions:
        screening_mark = "🤖" if question.is_for_screening else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"Вопрос №{question.order} {screening_mark}",
                callback_data=f"edit_question_{question.id}"
            )
        ])
    
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(
                text="◀️", 
                callback_data=f"questions_page_{vacancy_id}_{page-1}"
            ))
        pagination.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", 
            callback_data="noop"
        ))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(
                text="▶️", 
                callback_data=f"questions_page_{vacancy_id}_{page+1}"
            ))
        keyboard.append(pagination)
    
    keyboard.append([
        InlineKeyboardButton(
            text="➕ Создать новый вопрос",
            callback_data=f"create_question_{vacancy_id}"
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Отменить редактирование",
            callback_data=f"vacancy_detail_{vacancy_id}"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@admin_screening.callback_query(F.data.startswith("questions_page_"))
async def _handle_questions_pagination(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        vacancy_id = int(parts[2])
        page = int(parts[3])
        
        with Session() as db:
            questions = db.query(BotQuestion).filter_by(
                vacancy_id=vacancy_id
            ).order_by(BotQuestion.order).all()
            
            await callback.message.edit_reply_markup(
                reply_markup=_build_questions_keyboard(questions, vacancy_id, page=page)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error in questions pagination: {str(e)}')
        await handle_db_error(callback.message)


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
@admin_screening.callback_query(F.data.startswith("edit_question_"))
async def _edit_question_detail_menu(msg_or_query: Union[Message, CallbackQuery], question_id: int = None):
    try:
        if isinstance(msg_or_query, CallbackQuery):
            question_id = int(msg_or_query.data.split("_")[-1])
            msg_or_query = msg_or_query.message
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await msg_or_query.answer("Вопрос не найден")
                return
            
            screening_info = (
                f"\n\n🤖 Промпт для вопроса:\n{question.screening_criteria}"
                if question.is_for_screening and question.screening_criteria
                else "\n\n🤖 Промпт не настроен"
            )
            
            detail_text = (
                f"📝 Вопрос №{question.order}:\n\n"
                f"{question.question_text}"
                f"{screening_info}"
            )
            
            keyboard = [
                [InlineKeyboardButton(
                    text="✏️ Редактировать текст вопроса",
                    callback_data=f"edit_info_{question.id}_q"
                )],
                [InlineKeyboardButton(
                    text="🤖 Редактировать промпт для вопроса" if question.is_for_screening else "➕ Добавить промпт для вопроса",
                    callback_data=f"edit_info_{question.id}_p" if question.is_for_screening else f"add_screening_{question.id}"
                )],
                [InlineKeyboardButton(
                    text="🗑️ Удалить вопрос",
                    callback_data=f"delete_question_{question.id}"
                )],
                [InlineKeyboardButton(
                    text="🔙 Назад к списку вопросов",
                    callback_data=f"edit_vacancy_params_{question.vacancy_id}"
                )]
            ]

            try:
                await msg_or_query.edit_text(
                    detail_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            except:
                await msg_or_query.answer(
                    detail_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except Exception as e:
        logger.error(f'Error showing question detail: {str(e)}')
        await handle_db_error(msg_or_query)


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
                    question_texts += f'❓*Вопрос №{question.order}:* {question.question_text}\n'
                    question_texts += f'🤖 *Промпт:* {question.screening_criteria}\n\n'
                else:
                    question_texts += f'— *Q{question.order}:* {question.question_text}\n\n'
            
            await callback.message.answer(
                f'*Вопросы:*\n\n{question_texts}',
                parse_mode="Markdown"
            )
            await callback.answer()
    except Exception as e:
        logger.error(f'Error showing vacancy params details: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(F.data.startswith("edit_vacancy_params_"))
async def _edit_vacancy_params_menu(callback: CallbackQuery, vacancy_id: int = None):
    try:
        if not vacancy_id:
            vacancy_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancy = db.query(Vacancy).get(vacancy_id)
                
            if not vacancy:
                await callback.message.answer("Вакансия не найдена")
                return
            
            questions = db.query(BotQuestion).filter_by(
                vacancy_id=vacancy_id
            ).order_by(BotQuestion.order).all()
            if not questions:
                await callback.message.answer(
                    "У данной вакансии нет вопросов",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="➕ Создать вопросы",
                            callback_data=f"create_question_{vacancy_id}"
                        )],
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data=f"vacancy_detail_{vacancy_id}"
                        )]
                    ])
                )
                return
            
            await callback.message.edit_text(
                "📝 Редактирование вопросов вакансии:",
                reply_markup=_build_questions_keyboard(questions, vacancy_id)
            )
            await callback.answer()        
    except Exception as e:
            logger.error(f'Error editing vacancy params details: {str(e)}')
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
# Editing Handlers
#---------------
@admin_screening.callback_query(F.data.startswith("edit_info_"))
async def _edit_question_info(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_")
        # Callback data соответствует строке edit_info_{question_id}_{type}
        # Где type = ("p", "q") для p - промпта или q - вопроса, соответственно.
        type = parts[-1]
        question_id = int(parts[-2])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer("Вопрос не найден")
                return
            
            await state.update_data(question_id=question_id)
            if type == 'p':
                await state.set_state(QuestionEditingStates.waiting_for_screening_criteria)
                current_criteria = question.screening_criteria or "Не задано"
                await callback.message.edit_text(
                f"Текущий промпт для вопроса:\n\n{current_criteria}\n\n"
                "Введите новый промпт:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cancel_edit_{question_id}"
                        )]
                    ])
                )
                
            elif type == 'q':
                await state.set_state(QuestionEditingStates.waiting_for_new_text)
                await callback.message.edit_text(
                f"Текущий текст вопроса:\n\n{question.question_text}\n\n"
                "Введите новый текст вопроса:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cancel_edit_{question_id}"
                        )]
                    ])
                )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error starting screening criteria edit: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.message(StateFilter(QuestionEditingStates.waiting_for_new_text))
async def _process_new_question_text(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        question_id = data.get('question_id')
        
        if not message.text:
            await message.answer("Пожалуйста, введите текстовый ответ")
            return
            
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if question:
                question.question_text = message.text
                db.commit()
                
                await message.answer("Текст вопроса успешно обновлён")
                await state.clear()
                await _edit_question_detail_menu(message, question_id=question_id)
            else:
                await message.answer("Вопрос не найден")
                await state.clear()
    except Exception as e:
        logger.error(f'Error updating question text: {str(e)}')
        await state.clear()
        await handle_db_error(message)


@admin_screening.message(StateFilter(QuestionEditingStates.waiting_for_screening_criteria))
async def _process_new_screening_criteria(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        question_id = data.get('question_id')
        
        if not message.text:
            await message.answer("Пожалуйста, введите текстовый ответ")
            return
            
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if question:
                question.is_for_screening = True
                question.screening_criteria = message.text
                db.commit()
                
                await message.answer("Промпт успешно добавлен")
                await state.clear()
                await _edit_question_detail_menu(message, question_id=question_id)
            else:
                await message.answer("Вопрос не найден")
                await state.clear()
    except Exception as e:
        logger.error(f'Error updating screening criteria: {str(e)}')
        await state.clear()
        await handle_db_error(message)


@admin_screening.callback_query(F.data.startswith("add_screening_"))
async def _add_screening_criteria(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer("Вопрос не найден")
                return
                  
            await state.update_data(question_id=question_id)
            await state.set_state(QuestionEditingStates.waiting_for_screening_criteria)
            
            await callback.message.edit_text(
                "Добавление промпта:\n\n"
                "Введите текст промпта для скрининга ответа на этот вопрос:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cancel_edit_{question_id}"
                    )]
                ])
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error adding screening criteria: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(F.data.startswith("delete_question_"))
async def _delete_question(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer("Вопрос не найден")
                return
            
            await state.update_data(question_id=question_id)
            await state.set_state(QuestionEditingStates.confirming_delete)
            
            await callback.message.edit_text(
                f"Вы уверены, что хотите удалить этот вопрос?\n\n"
                f"Вопрос №{question.order}: {question.question_text}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Да, удалить",
                            callback_data=f"confirm_delete_{question_id}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Нет, отменить",
                            callback_data=f"cancel_delete_{question_id}"
                        )
                    ]
                ])
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error confirming question deletion: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(
    StateFilter(QuestionEditingStates.confirming_delete),
    F.data.startswith("confirm_delete_")
)
async def _confirm_delete_question(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer("Вопрос не найден")
                return
            
            vacancy_id = question.vacancy_id
            db.delete(question)
            db.commit()
            
            # Обновляем нумерацию для всех остальных вопросов по вакансии
            remaining_questions = db.query(BotQuestion).filter_by(
                vacancy_id=vacancy_id
            ).order_by(BotQuestion.order).all()
            
            for index, q in enumerate(remaining_questions, start=1):
                q.order = index
            db.commit()
            
            await callback.message.edit_text("Вопрос успешно удалён")
            await _edit_vacancy_params_menu(callback, vacancy_id=vacancy_id)
        
        await state.clear()
    except Exception as e:
        logger.error(f'Error deleting question: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Cancellation Handlers
#---------------
@admin_screening.callback_query(F.data.startswith("cancel_delete_"))
async def _cancel_delete_question(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[-1])
        await _edit_question_detail_menu(callback, question_id=question_id)
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(f'Error canceling question deletion: {str(e)}')
        await handle_db_error(callback.message)
        

@admin_screening.callback_query(F.data.startswith("cancel_edit_"))
async def _cancel_edit_question(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[-1])
        await _edit_question_detail_menu(callback, question_id=question_id)
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(f'Error canceling question edit: {str(e)}')
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