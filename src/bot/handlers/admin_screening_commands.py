import logging
import src.bot.utils.message_templates as msg_templates

from typing import List, Union, Optional
from sqlalchemy import desc, func
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
from src.database.models import Vacancy, Application, BotQuestion
from src.database.models.bot_question import AnswerFormat
from src.database.models.application import ApplicationStatus
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID
from src.bot.utils.error_handlers import handle_db_error


logger = logging.getLogger(__name__)
admin_screening = Router()


class QuestionEditingStates(StatesGroup):
    creating_new_question = State()
    choosing_question_type = State()
    
    waiting_for_question_text = State()
    waiting_for_choices = State()
    waiting_for_new_text = State()
    waiting_for_new_screening_criteria = State()
    waiting_for_screening_criteria = State()
    waiting_for_new_choices = State()
    
    confirming_delete_question_data = State()
    confirming_save = State()


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
            text=msg_templates.CREATE_NEW_QUESTION,
            callback_data=f"create_question_{vacancy_id}"
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            text=msg_templates.CANCEL_EDIT_VACANCY,
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
                await message.answer(msg_templates.NO_VACANCIES_IN_SYSTEM)
                return
            
            await message.answer(
                msg_templates.VACANCIES_LIST,
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
            if not question_id:
                question_id = int(msg_or_query.data.split("_")[-1])
            msg_or_query = msg_or_query.message
        
        with Session() as db:
            question: Optional[BotQuestion] = db.query(BotQuestion).get(question_id)
            if not question:
                await msg_or_query.answer(msg_templates.QUESTION_NOT_FOUND)
                return
            
            detail_text = msg_templates.vacancy_question_detail_message(
                question_order=question.order,
                question_text=question.question_text,
                choices=question.choices,
                is_for_screening=question.is_for_screening,
                screening_criteria=question.screening_criteria
            )
            
            keyboard = [
                [InlineKeyboardButton(
                    text=msg_templates.EDIT_QUESTION_TEXT,
                    callback_data=f"edit_info_{question.id}_q")],
                [InlineKeyboardButton(
                    text=msg_templates.EDIT_QUESTION_CHOICES if question.choices else msg_templates.ADD_QUESTION_CHOICES,
                    callback_data=f"edit_info_{question.id}_c" if question.choices else f"add_choices_{question.id}")]]

            keyboard.extend([[
                InlineKeyboardButton(
                    text=msg_templates.EDIT_QUESTION_PROMPT if question.is_for_screening else msg_templates.ADD_QUESTION_PROMPT,
                    callback_data=f"edit_info_{question.id}_p" if question.is_for_screening else f"add_screening_{question.id}")]])
            
            keyboard.extend([[
                InlineKeyboardButton(
                    text=msg_templates.EMPTY_BUTTON,
                    callback_data="noop")]])
            
            if question.choices:
                keyboard.append([InlineKeyboardButton(
                    text=msg_templates.DELETE_QUESTION_CHOICES,
                    callback_data=f"delete_question_{question.id}_c")])

            if question.screening_criteria:
                keyboard.append([InlineKeyboardButton(
                    text=msg_templates.DELETE_QUESTION_PROMPT,
                    callback_data=f"delete_question_{question.id}_p")])
                
            keyboard.extend([[InlineKeyboardButton(
                    text=msg_templates.DELETE_QUESTION,
                    callback_data=f"delete_question_{question.id}_q")]])

            keyboard.extend([[
                InlineKeyboardButton(
                    text=msg_templates.TO_QUESTIONS_LIST,
                    callback_data=f"edit_vacancy_params_{question.vacancy_id}")]])
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
                await callback.message.answer(msg_templates.VACANCY_NOT_FOUND)
                return
            
            questions = db.query(BotQuestion).filter_by(
                vacancy_id=vacancy_id
            ).order_by(BotQuestion.order).all()
            if not questions:
                await callback.message.answer(msg_templates.NO_QUESTIONS_FOR_VACANCY)
                return
            
            question_texts = ""
            for question in questions:
                answer_prompt = ""
                if question.choices:
                    answer_prompt += f'🔘 *Варианты ответов:* {" | ".join(question.choices)}\n'
                if question.is_for_screening:
                    answer_prompt += f'🤖 *Промпт:* {question.screening_criteria}\n'
                
                question_texts += (
                    f'❓*Вопрос №{question.order}:* {question.question_text}\n'
                    f'{answer_prompt}\n'
                )
            await callback.message.answer(
                f'*Вопросы:*\n\n{question_texts}',
                parse_mode="Markdown"
            )
            await callback.answer()
    except Exception as e:
        logger.error(f'Error showing vacancy params details: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(F.data.startswith("edit_vacancy_params_"))
async def _edit_vacancy_params_menu(msg_or_query: Union[Message, CallbackQuery], vacancy_id: int = None):
    try:
        if isinstance(msg_or_query, CallbackQuery):
            if not vacancy_id:
                vacancy_id = int(msg_or_query.data.split("_")[-1])
            msg_or_query = msg_or_query.message
  
        with Session() as db:
            vacancy = db.query(Vacancy).get(vacancy_id)
                
            if not vacancy:
                await msg_or_query.answer(msg_templates.VACANCY_NOT_FOUND)
                return
            
            questions = db.query(BotQuestion).filter_by(
                vacancy_id=vacancy_id
            ).order_by(BotQuestion.order).all()
            if not questions:
                await msg_or_query.answer(
                    msg_templates.NO_QUESTIONS_FOR_VACANCY,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text=msg_templates.CREATE_NEW_QUESTION,
                            callback_data=f"create_question_{vacancy_id}"
                        )],
                        [InlineKeyboardButton(
                            text=msg_templates.BACK_TO_LIST,
                            callback_data=f"vacancy_detail_{vacancy_id}")]])
                    )
                return
            
            try:
                await msg_or_query.edit_text(
                    msg_templates.EDITING_VACANCY_QUESTIONS,
                    reply_markup=_build_questions_keyboard(questions, vacancy_id))
            except:
                await msg_or_query.answer(
                    msg_templates.EDITING_VACANCY_QUESTIONS,
                    reply_markup=_build_questions_keyboard(questions, vacancy_id))
    except Exception as e:
            logger.error(f'Error editing vacancy params details: {str(e)}')
            await handle_db_error(msg_or_query)
            

@admin_screening.callback_query(F.data.startswith("vacancy_detail_"))
async def _show_vacancy_detail(callback: CallbackQuery):
    try:
        vacancy_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancy = db.query(Vacancy).get(vacancy_id)
            if not vacancy:
                await callback.answer(msg_templates.VACANCY_NOT_FOUND)
                return
            
            status_counts = db.query(
                Application.status,
                func.count(Application.id)
            ).filter(
                Application.vacancy_id == vacancy_id
            ).group_by(
                Application.status
            ).all()
            count_dict = {status: count for status, count in status_counts}
            
            application_count = sum(count_dict.values())
            active_application_count = count_dict.get(ApplicationStatus.ACTIVE, 0)
            review_application_count = count_dict.get(ApplicationStatus.REVIEW, 0)
            approved_application_count = count_dict.get(ApplicationStatus.ACCEPTED, 0)
            declined_application_count = count_dict.get(ApplicationStatus.REJECTED, 0)
            
            detail_text = msg_templates.vacancy_detail_message(
                title=vacancy.title,
                description=vacancy.description,
                all=application_count,
                active=active_application_count,
                review=review_application_count,
                approved=approved_application_count,
                declined=declined_application_count
            )
              
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=msg_templates.VIEW_VACANCY_PARAMS,
                    callback_data=f"vacancy_params_{vacancy_id}"
                )],
                
                [InlineKeyboardButton(
                    text=msg_templates.EDIT_VACANCY_PARAMS,
                    callback_data=f"edit_vacancy_params_{vacancy_id}"
                )],
                
                [InlineKeyboardButton(
                    text=msg_templates.EMPTY_BUTTON,
                    callback_data=f"noop"
                )],
                # TODO: Implement
                [InlineKeyboardButton(
                    text=msg_templates.VIEW_RESUME_SCREENING_PARAMS,
                    callback_data=f"noop"
                )],
                # TODO: Implement
                [InlineKeyboardButton(
                    text=msg_templates.EDIT_RESUME_SCREENING_PARAMS,
                    callback_data=f"noop"
                )],

                [InlineKeyboardButton(
                    text=msg_templates.BACK_TO_LIST,
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
                msg_templates.VACANCIES_LIST,
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
        # Где type = ("p", "q", "c") для p - промпта,  q - вопроса, c - вариантов ответа соответственно.
        type = parts[-1]
        question_id = int(parts[-2])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer(msg_templates.QUESTION_NOT_FOUND)
                return
            
            await state.update_data(question_id=question_id)
            if type == 'p':
                await state.set_state(QuestionEditingStates.waiting_for_screening_criteria)
                current_criteria = question.screening_criteria or "Не задано"
                await callback.message.edit_text(
                text=msg_templates.edit_prompt_message(current_criteria),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=msg_templates.CANCEL_EDIT_VACANCY,
                        callback_data=f"cancel_op_{question_id}"
                        )]
                    ]
                ), 
                parse_mode="Markdown"
            )
                
            elif type == 'q':
                await state.set_state(QuestionEditingStates.waiting_for_new_text)
                await callback.message.edit_text(
                text=msg_templates.edit_question_text_message(question.question_text),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=msg_templates.CANCEL_EDIT_VACANCY,
                        callback_data=f"cancel_op_{question_id}"
                        )]
                    ])
                )
            
            elif type == 'c':
                await state.set_state(QuestionEditingStates.waiting_for_new_choices)
                await callback.message.edit_text(
                text=msg_templates.edit_choices_message(question.choices),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=msg_templates.CANCEL_EDIT_VACANCY,
                        callback_data=f"cancel_op_{question_id}"
                        )]
                    ]),
                parse_mode="Markdown"             
                )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error starting screening criteria edit: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Create Question
#---------------
@admin_screening.callback_query(F.data.startswith("create_question_"))
async def _create_new_question(callback: CallbackQuery, state: FSMContext):
    try:
        vacancy_id = int(callback.data.split("_")[-1])
        with Session() as db:
            vacancy: Optional[Vacancy] = db.query(Vacancy).get(vacancy_id)
            if not vacancy:
                await callback.answer(msg_templates.VACANCY_NOT_FOUND)
                return
                  
            await state.update_data(vacancy_id=vacancy_id)
            await state.set_state(QuestionEditingStates.choosing_question_type)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=msg_templates.TEXT_TYPE,
                    callback_data="question_type_text"
                )],
                
                [InlineKeyboardButton(
                    text=msg_templates.CHOICES_TYPE,
                    callback_data="question_type_choice"
                )],

                [InlineKeyboardButton(
                    text=msg_templates.CANCEL_QUESTION_CREATION,
                    callback_data=f"vacancy_detail_{vacancy_id}"
                )]])    
                
            await callback.message.edit_text(
                    "Выберите тип вопроса:",
                    reply_markup=keyboard
                )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error creating new question: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(
    StateFilter(QuestionEditingStates.choosing_question_type),
    F.data.startswith("question_type_")
)
async def _handle_question_type_selection(callback: CallbackQuery, state: FSMContext):
    try:
        question_type = callback.data.split("_")[-1]
        data = await state.get_data()
        await state.update_data(question_type=question_type)
        await state.set_state(QuestionEditingStates.waiting_for_question_text)
        
        await callback.message.edit_text(
            "Введите текст вопроса:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=msg_templates.CANCEL_QUESTION_CREATION,
                    callback_data=f"vacancy_detail_{data.get('vacancy_id')}"
                )]
            ])
        )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error handling question type selection: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.message(StateFilter(QuestionEditingStates.waiting_for_question_text))
async def _process_question_text(message: Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer(msg_templates.INCORRECT_INPUT_PROVIDED)
            return
            
        data = await state.get_data()
        question_type = data.get('question_type')
        
        await state.update_data(question_text=message.text)
        
        if question_type == 'choice':
            await state.set_state(QuestionEditingStates.waiting_for_choices)
            await message.answer(
                "Введите варианты ответов, *через запятую*:\n"
                "*Пример:* 'полный день, гибкий график, удалённая работа'",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=msg_templates.CANCEL_QUESTION_CREATION,
                        callback_data=f"vacancy_detail_{data.get('vacancy_id')}"
                    )]
                ]),
                parse_mode="Markdown"
            )
        else:
            await state.set_state(QuestionEditingStates.confirming_save)
            await _show_save_confirmation(message, state)
    except Exception as e:
        logger.error(f'Error processing question text: {str(e)}')
        await handle_db_error(message)


@admin_screening.message(StateFilter(QuestionEditingStates.waiting_for_choices))
async def _process_question_choices(message: Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer(
                "Пожалуйста, введите варианты ответов *через запятую*", 
                parse_mode="Markdown"
            )
            return
            
        choices = [choice.strip().capitalize() for choice in message.text.split(',')]
        await state.update_data(choices=choices)
        await state.set_state(QuestionEditingStates.confirming_save)
        await _show_save_confirmation(message, state)
    except Exception as e:
        logger.error(f'Error processing question choices: {str(e)}')
        await handle_db_error(message)


async def _show_save_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    question_text = data.get('question_text')
    choices = data.get('choices', [])
    
    text = f"📝 Новый вопрос:\n\n{question_text}\n"
    if choices:
        text += f"\nВарианты ответов: {' | '.join(choices)}\n"
    
    keyboard = [
        [InlineKeyboardButton(
            text=msg_templates.SAVE_QUESTION,
            callback_data="save_question"
        )],
        [InlineKeyboardButton(
            text=msg_templates.ADD_PROMPT,
            callback_data="add_screening_to_question"
        )],
        [InlineKeyboardButton(
            text=msg_templates.CANCEL_QUESTION_CREATION,
            callback_data=f"vacancy_detail_{data.get('vacancy_id')}"
        )]
    ]
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@admin_screening.callback_query(
    StateFilter(QuestionEditingStates.confirming_save),
    F.data == "save_question"
)
async def _save_new_question(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        vacancy_id = data.get('vacancy_id')
        question_text = data.get('question_text')
        question_type = data.get('question_type')
        choices = data.get('choices', [])
        
        with Session() as db:
            max_order = db.query(func.max(BotQuestion.order)).filter_by(
                vacancy_id=vacancy_id
            ).scalar() or 0
            
            new_question = BotQuestion(
                vacancy_id=vacancy_id,
                question_text=question_text,
                order=max_order + 1,
                expected_format=AnswerFormat.CHOICE if question_type == 'choice' else AnswerFormat.TEXT,
                choices=choices if question_type == 'choice' else None,
                is_for_screening=False
            )
            
            db.add(new_question)
            db.commit()
            
            await callback.message.edit_text(msg_templates.QUESTION_SAVED)
            await _edit_vacancy_params_menu(callback, vacancy_id=vacancy_id)
        
        await state.clear()
    except Exception as e:
        logger.error(f'Error saving new question: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(
    StateFilter(QuestionEditingStates.confirming_save),
    F.data == "add_screening_to_question"
)
async def _add_screening_to_new_question(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        await state.set_state(QuestionEditingStates.waiting_for_new_screening_criteria)
        
        await callback.message.edit_text(
            text=(
                f'{msg_templates.PROMPT_CREATE_HELPER}'
                "🤖 *Введите новый промпт:*"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=msg_templates.CANCEL_QUESTION_CREATION,
                    callback_data=f"vacancy_detail_{data.get('vacancy_id')}"
                )]
            ]),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error adding screening to new question: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.message(StateFilter(QuestionEditingStates.waiting_for_new_screening_criteria))
async def _process_new_question_screening(message: Message, state: FSMContext):
    try:
        if not message.text:
            await message.answer(
                f"{msg_templates.PROMPT_CREATE_HELPER}"
                "🤖 *Введите новый промпт:*",
                parse_mode="Markdown"
            )
            return
            
        data = await state.get_data()
        vacancy_id = data.get('vacancy_id')
        question_text = data.get('question_text')
        question_type = data.get('question_type')
        choices = data.get('choices', [])
        
        with Session() as db:
            max_order = db.query(func.max(BotQuestion.order)).filter_by(
                vacancy_id=vacancy_id
            ).scalar() or 0
            
            new_question = BotQuestion(
                vacancy_id=vacancy_id,
                question_text=question_text,
                order=max_order + 1,
                expected_format=AnswerFormat.CHOICE if question_type == 'choice' else AnswerFormat.TEXT,
                choices=choices if question_type == 'choice' else None,
                is_for_screening=True,
                screening_criteria=message.text
            )
            
            db.add(new_question)
            db.commit()
            
            await message.answer(msg_templates.QUESTION_SAVED)
            await _edit_vacancy_params_menu(message, vacancy_id=vacancy_id)
        
        await state.clear()
    except Exception as e:
        logger.error(f'Error saving new question with screening: {str(e)}')
        await handle_db_error(message)


#---------------
# Edit Question Text
#---------------
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
                
                await message.answer("✅ Текст вопроса успешно обновлён")
                await state.clear()
                await _edit_question_detail_menu(message, question_id=question_id)
            else:
                await message.answer(msg_templates.QUESTION_NOT_FOUND)
                await state.clear()
    except Exception as e:
        logger.error(f'Error updating question text: {str(e)}')
        await state.clear()
        await handle_db_error(message)


#---------------
# Edit Question Choices
#---------------
@admin_screening.message(StateFilter(QuestionEditingStates.waiting_for_new_choices))
async def _process_new_choices_text(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        question_id = data.get('question_id')
        
        if not message.text:
            await message.answer(
                "Пожалуйста, введите варианты ответа текстом, *через запятую*",
                parse_mode="Markdown"
            )
            return
        
        with Session() as db:
            question: Optional[BotQuestion] = db.query(BotQuestion).get(question_id)
            
            if question:
                if question.expected_format == AnswerFormat.TEXT:
                    question.expected_format = AnswerFormat.CHOICE

                choices = [choice.strip().capitalize() for choice in message.text.split(',')]
                question.choices = choices
                db.commit()

                await message.answer("✅ Варианты ответов успешно обновлены")
                await state.clear()
                await _edit_question_detail_menu(message, question_id=question_id)
            else:
                await message.answer(msg_templates.QUESTION_NOT_FOUND)
                await state.clear()
    except Exception as e:
        logger.error(f'Error updating question choices: {str(e)}')
        await state.clear()
        await handle_db_error(message)


@admin_screening.callback_query(F.data.startswith("add_choices_"))
async def _add_question_choices(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            question: Optional[BotQuestion] = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer(msg_templates.QUESTION_NOT_FOUND)
                return
                  
            await state.update_data(question_id=question_id)
            await state.set_state(QuestionEditingStates.waiting_for_new_choices)
            
            await callback.message.edit_text(
                "Добавление вариантов ответа:\n\n"
                "❗️Введите варианты ответа на вопрос, *через запятую (регистр не имеет значение)*\n"
                "*Пример:* 'полный день, гибкий график, удаленная работа' - распознается как 3 варианта ответа",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cancel_op_{question_id}"
                    )]
                ]),
                parse_mode="Markdown"
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error adding question choices: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Edit Question Screening
#---------------
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
                
                await message.answer("✅ Промпт успешно добавлен")
                await state.clear()
                await _edit_question_detail_menu(message, question_id=question_id)
            else:
                await message.answer(msg_templates.QUESTION_NOT_FOUND)
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
                await callback.answer(msg_templates.QUESTION_NOT_FOUND)
                return
                  
            await state.update_data(question_id=question_id)
            await state.set_state(QuestionEditingStates.waiting_for_screening_criteria)
            
            await callback.message.edit_text(
                "Добавление промпта:\n\n"
                f"{msg_templates.PROMPT_CREATE_HELPER}"
                "🤖 *Введите текст промпта:*",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=msg_templates.CANCEL_EDIT_VACANCY,
                        callback_data=f"cancel_op_{question_id}"
                    )]
                ]),parse_mode="Markdown"
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error adding screening criteria: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Delete Question
#---------------
@admin_screening.callback_query(F.data.startswith("delete_question_"))
async def _delete_question_data(callback: CallbackQuery, state: FSMContext):
    try:
        _, _, question_id_str, op = callback.data.split("_")
        question_id = int(question_id_str)
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer(msg_templates.QUESTION_NOT_FOUND)
                return
            
            detail_text = ""
            q_order = question.order
            q_text = question.question_text
            await state.update_data(question_id=question_id)
            await state.set_state(QuestionEditingStates.confirming_delete_question_data)
            
            if op == "q":
                detail_text = (
                    f"*Вы уверены, что хотите удалить вопрос?*\n\n"
                    f"Вопрос №{q_order}: {q_text}"
                )
            elif op == "c":
                detail_text = (
                    f"*Вы уверены, что хотите удалить варианты к вопросу?*\n\n"
                    f"Вопрос №{q_order}: {q_text}"
                )
            elif op == "p":
                detail_text = (
                    f"*Вы уверены, что хотите удалить промпт для вопроса?*\n\n"
                    f"Вопрос №{q_order}: {q_text}"
                )
            else:
                await callback.answer(msg_templates.INCORRECT_QUESTION_OPERATION)
                return
                
            await callback.message.edit_text(
                detail_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Да, удалить",
                            callback_data=f"confirm_delete_{question_id}_{op}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Нет, отменить операцию",
                            callback_data=f"cancel_op_{question_id}"
                        )
                    ]
                ]),
                parse_mode="Markdown"
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error confirming question data deletion: {str(e)}')
        await handle_db_error(callback.message)


@admin_screening.callback_query(
    StateFilter(QuestionEditingStates.confirming_delete_question_data),
    F.data.startswith("confirm_delete_")
)
async def _confirm_delete_question_data(callback: CallbackQuery, state: FSMContext):
    try:
        _, _, question_id_str, op = callback.data.split("_")
        question_id = int(question_id_str)
        
        with Session() as db:
            question: Optional[BotQuestion] = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer(msg_templates.QUESTION_NOT_FOUND)
                return
            
            if op == "q":
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
                
                await callback.message.edit_text("🗑️ Вопрос успешно удален")
                await _edit_vacancy_params_menu(callback, vacancy_id=vacancy_id)
            
            elif op == "c":
                question.choices = None
                question.expected_format = AnswerFormat.TEXT
                db.commit()
                
                await callback.message.edit_text("🗑️ Варианты ответа успешно удалены")
                await _edit_question_detail_menu(callback, question_id=question_id)
                
            elif op == "p":
                question.screening_criteria = None
                question.is_for_screening = False
                db.commit()
                
                await callback.message.edit_text("🗑️ Промпт успешно удален")
                await _edit_question_detail_menu(callback, question_id=question_id)
                
            else:
                await callback.answer(msg_templates.INCORRECT_QUESTION_OPERATION)
                return
        await state.clear()
    except Exception as e:
        logger.error(f'Error deleting question data: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Cancellation Handlers
#---------------
@admin_screening.callback_query(F.data.startswith("cancel_op_"))
async def _cancel_operation_on_question(callback: CallbackQuery, state: FSMContext):
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