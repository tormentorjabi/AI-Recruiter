import logging
import src.bot.utils.message_templates as msg_templates

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import and_
from datetime import datetime, timedelta, timezone

from src.database.session import Session
from src.database.models import (
    Candidate, Application, BotQuestion, HrNotification,
    Vacancy, BotInteraction, AnalysisResult
)

from src.bot.utils.bot_answers_json_builder import build_json
from src.bot.utils.schedule_form_reminder import schedule_form_reminder
from src.bot.utils.handle_error import handle_db_error

from src.database.models.application import ApplicationStatus
from src.database.models.bot_interaction import InteractionState
from src.database.models.bot_question import AnswerFormat

from src.gigachat_module.telegram_screening import TelegramScreening


logger = logging.getLogger(__name__)
candidate_router = Router()

class CandidateStates(StatesGroup):
    token_auth = State()
    answering = State()
    review = State()
    editing = State()


# --------------------------
#  Core Utilities
# --------------------------
# async def handle_db_error(message: Message, error_msg: str = "Произошла ошибка"):
#     '''Лог ошибок, возникающих в результате ошибок БД'''
#     await message.answer(f"⚠️ {error_msg}. Попробуйте позже.")
#     logger.error(error_msg)


async def _update_last_active(candidate_id: int, application_id: int):
    try:
        with Session() as db:
            interaction = db.query(BotInteraction).filter_by(
                candidate_id=candidate_id,
                application_id=application_id
            ).first()
            if interaction:
                interaction.last_active = datetime.utcnow()
                db.commit()
    except Exception as e:
        logger.error(f"Error updating last_active: {str(e)}")


async def _get_current_interaction_data(state: FSMContext):
    '''Быстрое получение сохраненных значений из FSMContext state'''
    data = await state.get_data()
    return {
        'candidate_id': data.get('candidate_id'),
        'application_id': data.get('application_id'),
        'vacancy_id': data.get('vacancy_id', ''),
        'vacancy_title': data.get('vacancy_title', ''),
        'current_question': data.get('current_question', 0),
        'questions': data.get('questions', []),
        'answers': data.get('answers', {})
    }


async def _update_interaction_state(application_id: int, state_data: dict):
    '''
        Обновление BotInteraction instance данных об текущих ответах кандидата,
        текущем ID вопроса и последней отметке активности
    '''
    with Session() as db:
        interaction = db.query(BotInteraction).filter_by(
            application_id=application_id
        ).first()
        if interaction:
            interaction.answers = state_data['answers']
            interaction.current_question_id = state_data['questions'][state_data['current_question']]
            interaction.last_active = datetime.utcnow()
            db.commit()


# --------------------------
#  Question Display Utilities
# --------------------------
def _build_choice_keyboard(choices, callback_prefix, cancel_text="❌ Отменить", is_editing=False):
    '''Сборка Inline клавиатуры для вопросов с выбором ответа'''
    if len(choices) > 4:
        keyboard = [
            [InlineKeyboardButton(text=choice, callback_data=f"{callback_prefix}_{i}") 
             for choice in choices[i:i+2]]
            for i in range(0, len(choices), 2)
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text=choice, callback_data=f"{callback_prefix}_{i}")]
            for i, choice in enumerate(choices)
        ]
    
    cancel_callback = "cancel_edit" if is_editing else "cancel_process"
    keyboard.append([InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def _build_review_keyboard(questions, current_page, total_pages):
    '''Сборка Inline клавиатуры для меню финальной сверки ответов'''
    keyboard = [
        [InlineKeyboardButton(text=f"✏️ Вопрос {i+1 + current_page*5}", callback_data=f"edit_{q.id}")]
        for i, q in enumerate(questions)
    ]
    
    if total_pages > 1:
        pagination = []
        if current_page > 0:
            pagination.append(InlineKeyboardButton(text="◀️", callback_data=f"review_page_{current_page-1}"))
        pagination.append(InlineKeyboardButton(text=f"{current_page+1}/{total_pages}", callback_data="noop"))
        if current_page < total_pages - 1:
            pagination.append(InlineKeyboardButton(text="▶️", callback_data=f"review_page_{current_page+1}"))
        keyboard.append(pagination)
    
    keyboard.extend([
        [InlineKeyboardButton(text="✅ Подтвердить отправку", callback_data="submit_answers")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_process")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def _show_question(question: BotQuestion, message: Message, state: FSMContext):
    '''Показать текущий вопрос кандидату'''
    try:
        data = await state.get_data()
        current_num = data['current_question'] + 1
        total = len(data['questions'])
        
        if question.expected_format == AnswerFormat.CHOICE and question.choices:
            # Для вопросов с вариантами ответов, нужно собрать Inline клавиатуру с вариантами
            # ответов
            await message.answer(
                f"Вопрос {current_num}/{total}:\n\n{question.question_text}\n\n🎯 Выберите вариант ответа",
                reply_markup=_build_choice_keyboard(question.choices, "choice")
            )
        else:
            format_hint = {
                AnswerFormat.TEXT: "✍️ Введите текстовый ответ",
                AnswerFormat.FILE: "📎 Отправьте файл"
            }.get(question.expected_format, "")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Следующий вопрос", callback_data="next_question")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_process")]
            ])
            
            await message.answer(
                f"Вопрос {current_num}/{total}:\n\n{question.question_text}\n\n{format_hint}",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error showing question: {str(e)}")
        raise


# --------------------------
#  Review Utilities
# --------------------------
async def _build_review_content(questions, answers):
    '''Сборка контента всех ответов кандидата для меню финальной сверки'''
    review_content = []
    for idx, q in enumerate(questions):
        answer = answers.get(str(q.id), 'Нет ответа')
        if q.expected_format == AnswerFormat.FILE and answer.startswith("FILE:"):
            answer = "Прикрепленный файл"
        review_content.append(f"{idx+1}. {q.question_text}\nОтвет: {answer}")
    return "\n\n".join(review_content)


async def handle_review(message: Message, state: FSMContext, page: int = 0):
    '''Обработка финальной сверки всех ответов кандидата'''
    try:
        data = await state.get_data()
        QUESTIONS_PER_PAGE = 5
        
        with Session() as db:
            # Достаем все вопросы по вакансии
            questions = db.query(BotQuestion).filter(
                BotQuestion.id.in_(data['questions'])
            ).order_by(BotQuestion.order).all()
            # Собирает данные с ответами
            content = await _build_review_content(questions, data['answers'])
            # В случае большого количества вопросов, зависит от [QUESTIONS_PER_PAGE]
            # готовимся к клавиатуре с пагинацией
            page_questions = questions[page*QUESTIONS_PER_PAGE:(page+1)*QUESTIONS_PER_PAGE]
            total_pages = (len(questions) + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE
            # Собираем клавиатуру финальной сверки
            keyboard = await _build_review_keyboard(page_questions, page, total_pages)

            if hasattr(message, 'message_id'):
                await message.answer(f"📝 Ваши ответы:\n\n{content}", reply_markup=keyboard)
            else:
                logger.warning(f'{message} has no "message_id": This behaviour is unexpected!')
                await message.answer(f"📝 Ваши ответы:\n\n{content}", reply_markup=keyboard)
            
            await state.set_state(CandidateStates.review)
            await state.update_data(review_page=page)
            
    except Exception as e:
        with Session() as db:
            interaction = db.query(BotInteraction).filter_by(
                application_id=data['application_id']
            ).first()
            interaction.state=InteractionState.PAUSED
            db.commit()
        
        logger.error(f"Review error: {str(e)}")
        await handle_db_error(message)


# --------------------------
#  Common Handlers
# --------------------------
@candidate_router.message(
    StateFilter(CandidateStates.token_auth),
    # Внимание!
    # Проверка работает с token_urlsafe(32) токенами.
    # При изменении длины токена или метода генерации, 
    # нужно изменить фильтрацию.
    F.text.regexp(r'^[a-zA-Z0-9_-]{43}$')
)
async def handle_token_auth(message: Message, state: FSMContext):
    '''Обработка идентификации кандидата по его токену'''
    try:
        token = message.text.strip()
        current_time = datetime.utcnow()
        telegram_id = str(message.from_user.id)
        
        with Session() as db:
            # Ищем отклик по отправленному токену
            application = db.query(Application).filter(
                Application.auth_token == token,
                Application.token_expiry > current_time
            ).first()
            
            if not application:
                await message.answer(msg_templates.TOKEN_AUTH_INVALID)
                return
            
            # Получаем кандидата по отклику 
            candidate = db.query(Candidate).get(application.candidate_id)
            if not candidate:
                await message.answer(msg_templates.CANDIDATE_NOT_FOUND)
                return
            
            # Дополняем информацию о Telegram ID
            candidate.telegram_id = telegram_id
            
            db.commit()
            
            # Уведомляем кандидата об успешной идентификации его в система
            await message.answer(
                msg_templates.TOKEN_AUTH_SUCCESS,
                parse_mode="Markdown"
            )
            await state.clear()
            # Переходим к сценарию прохождения анкеты
            await candidate_start(message, state)
        
    except Exception as e:
        logger.error(f'Error in handle_token_auth: {str(e)}')
        await handle_db_error(message, "Ошибка при проверке токена кандидата")


@candidate_router.message(Command('cancel'))
@candidate_router.callback_query(F.data == 'cancel_process')
async def cancel_interaction(query_or_msg: Message | CallbackQuery, state: FSMContext):
    '''Отмена прохождения опроса кандидатом'''
    try:
        message = query_or_msg.message if isinstance(query_or_msg, CallbackQuery) else query_or_msg
        data = await state.get_data()
        
        if not data or 'candidate_id' not in data or 'application_id' not in data:
            await message.answer(
                msg_templates.NO_ACTIVE_SESSION_FOUND_TO_CANCEL,
                parse_mode="Markdown"
            )
            return
        
        if data.get('current_question', 0) >= 0:
            try:
                with Session() as db:
                    interaction = db.query(BotInteraction).filter_by(
                        candidate_id=data['candidate_id'],
                        application_id=data['application_id']
                    ).first()
                    
                    if interaction:
                        interaction.state = InteractionState.PAUSED
                        interaction.current_question_id = data['questions'][data['current_question']]
                        db.commit()
                        
                        # Создаем напоминание для пользователя (default = 30 минут)
                        bot = message.bot
                        user_id = message.chat.id
                        await schedule_form_reminder(
                            bot=bot,
                            user_id=user_id,
                            application_id=data['application_id']
                        )
            except Exception as e:
                logger.error(f"Error saving paused state: {str(e)}")

        await state.clear()
        await message.answer(
            msg_templates.CANDIDATE_CANCELLED_FORM,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Cancel error: {str(e)}")
        await handle_db_error(message)


@candidate_router.message(Command("start"))
async def candidate_start(message: Message, state: FSMContext):
    '''Начать или возобновить диалог'''
    try:
        telegram_id = str(message.from_user.id)
        
        with Session() as db:
            candidate = db.query(Candidate).filter(
                Candidate.telegram_id == telegram_id
            ).first()
            
            if not candidate:
                await message.answer(
                    msg_templates.NOT_REGISTERED_AS_HR,
                    parse_mode="Markdown"
                )
                await message.answer(msg_templates.TOKEN_AUTH_REQUEST)
                await state.set_state(CandidateStates.token_auth)
                return

            application = db.query(Application).filter(
                and_(
                    Application.candidate_id == candidate.id,
                    Application.status == ApplicationStatus.ACTIVE
                )
            ).join(Vacancy).first()
            
            if not application:
                await message.answer(
                    msg_templates.CANDIDATE_APPLICATIONS_NOT_FOUND
                )
                return

            await _update_last_active(
                candidate_id=candidate.id, 
                application_id=application.id
            )
            
            interaction = db.query(BotInteraction).filter(
                BotInteraction.application_id == application.id
            ).order_by(BotInteraction.id.asc()).first()
            
            questions = db.query(BotQuestion).filter(
                BotQuestion.vacancy_id == application.vacancy_id
            ).order_by(BotQuestion.order).all()
            
            if not questions:
                await message.answer(
                    msg_templates.VACANCY_QUESTIONS_NOT_FOUND
                )
                return

            if interaction and interaction.state == InteractionState.PAUSED:
                # Ответы кандидата хранятся 24 часов, затем форму нужно заполнять с начала
                if (datetime.utcnow() - interaction.last_active) > timedelta(hours=24):
                    db.delete(interaction)
                    db.commit()
                    await message.answer(
                        msg_templates.CANDIDATE_BOT_INTERACTION_SESSION_TIMEOUT
                    )
                    return
                # Заполняем FSMContext state данными об единице интерактива 
                state_data = {
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.full_name,
                    'application_id': application.id,
                    'vacancy_id': application.vacancy_id,
                    'vacancy_title': application.vacancy.title,
                    'questions': [q.id for q in questions],
                    'answers': interaction.answers or {},
                    'current_question': next(
                    (i for i, q in enumerate(questions) 
                     if q.id == interaction.current_question_id), 0
                    ),
                    'resumed': True
                }
                # Возобновляем интерактив
                interaction.state = InteractionState.STARTED
                resume_question = questions[state_data['current_question']]
                await message.answer("🔄 Возобновляем ваше предыдущее заполнение формы")
            else:
                # Создаем новую, пустую единицу интерактива
                interaction = BotInteraction(
                    candidate_id=candidate.id,
                    application_id=application.id,
                    current_question_id=questions[0].id,
                    vacancy_id=application.vacancy_id,
                    state=InteractionState.STARTED,
                    last_active=datetime.utcnow()
                )
                db.add(interaction)
                # Заполняем FSMContext state данными об единице интерактива
                state_data = {
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.full_name,
                    'application_id': application.id,
                    'vacancy_id': application.vacancy_id,
                    'vacancy_title': application.vacancy.title,
                    'questions': [q.id for q in questions],
                    'answers': {},
                    'current_question': 0,
                    'resumed': False
                }
                resume_question = questions[0]
            
            db.commit()
            await state.set_data(state_data)
            # Приветственное сообщение для кандидата
            await message.answer(
                msg_templates.get_candidate_on_start_bot_interaction_message(
                    db_candidate_full_name=candidate.full_name,
                    vacancy_title=application.vacancy.title,
                    questions_length=len(questions)),
                parse_mode="Markdown"
            )
            # Начинаем показ вопросов из банка вопросов
            await _show_question(resume_question, message, state)
            await state.set_state(CandidateStates.answering)

    except Exception as e:
        logger.error(f"Start error: {str(e)}")
        await handle_db_error(message)


# --------------------------
#  Question Navigation
# --------------------------
@candidate_router.callback_query(F.data == "next_question", CandidateStates.answering)
async def handle_next_question(callback: CallbackQuery, state: FSMContext):
    '''Обработка подготовки к следующему вопросу'''
    try:
        data = await _get_current_interaction_data(state)
        # Если вопросы закончились, переходим к финальной сверке ответов
        if data['current_question'] >= len(data['questions']) - 1:
            return await handle_review(callback.message, state)

        with Session() as db:
            next_question_id = data['questions'][data['current_question'] + 1]
            next_question = db.query(BotQuestion).get(next_question_id)
            
            data['current_question'] += 1
            await _update_interaction_state(data['application_id'], data)
            await state.update_data(current_question=data['current_question'])
            await _show_question(next_question, callback.message, state)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Next question error: {str(e)}")
        await handle_db_error(callback.message)


async def handle_next_question_auto(message: Message, state: FSMContext):
    '''Инициализация показа следующего вопроса из списка вопросов'''
    try:
        data = await _get_current_interaction_data(state)
        with Session() as db:
            next_question = db.query(BotQuestion).get(data['questions'][data['current_question'] + 1])
            await state.update_data(current_question=data['current_question'] + 1)
            await _show_question(next_question, message, state)
    except Exception as e:
        logger.error(f"Auto next error: {str(e)}")
        await handle_db_error(message)


@candidate_router.callback_query(F.data.startswith("review_page_"))
async def handle_review_pagination(callback: CallbackQuery, state: FSMContext):
    '''Обработка пагинации на финальной сверке ответов'''
    try:
        page = int(callback.data.split("_")[-1])
        await handle_review(callback.message, state, page)
        await callback.answer()
    except Exception as e:
        logger.error(f"Pagination error: {str(e)}")
        await handle_db_error(callback.message)


# --------------------------
#  Answer Handling
# --------------------------
@candidate_router.message(CandidateStates.answering)
async def handle_text_answer(message: Message, state: FSMContext):
    '''Обработка ответа кандидата'''
    try:
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
        await _update_last_active(
                candidate_id=data['candidate_id'], 
                application_id=data['application_id']
        )
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await message.answer(msg_templates.QUESTION_NOT_FOUND)
                return

            if question.expected_format == AnswerFormat.CHOICE:
                await message.answer("ℹ️ Пожалуйста, выберите вариант из предложенных")
                return

            answer_content = await _process_answer_content(message, question)
            if not answer_content:
                return

            await _update_answer(state, data, question_id, answer_content)
            
            if await state.get_state() == CandidateStates.editing:
                # Если пришел из меню финальной сверки, отправляем назад
                await handle_review(message, state)
                await state.set_state(CandidateStates.review)
            elif data['current_question'] < len(data['questions']) - 1:
                # Если ещё есть вопросы, автоматически показывает новый вопрос
                await handle_next_question_auto(message, state)
            else:
                # Иначе конец интерактива - идём в меню финальной сверки
                await handle_review(message, state)

    except Exception as e:
        logger.error(f"Answer error: {str(e)}")
        await handle_db_error(message)


async def _process_answer_content(message: Message, question: BotQuestion):
    '''Получение содержимого ответа, введенного кандидатом'''
    if question.expected_format == AnswerFormat.FILE:
        if not message.document:
            await message.answer(msg_templates.FILE_EXPECTED)
            return None
        return f"FILE:{message.document.file_id}"
    return message.text


async def _update_answer(state: FSMContext, data: dict, question_id: int, answer: str):
    '''Добавление ответа кандидата в список сохраненных ответов'''
    new_answers = {**data['answers'], str(question_id): answer}
    await state.update_data(answers=new_answers)
    await _update_interaction_state(data['application_id'], {
        **data,
        'answers': new_answers
    })


@candidate_router.callback_query(F.data.startswith("choice_"))
async def handle_choice_answer(callback: CallbackQuery, state: FSMContext):
    '''Обработка ответа кандидата на вопрос, с выбором ответа'''
    try:
        choice_idx = int(callback.data.split("_")[1])
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
        await _update_last_active(
                candidate_id=data['candidate_id'], 
                application_id=data['application_id']
        )
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question or not question.choices:
                await callback.answer("❌ Неверный вариант")
                return

            selected_choice = question.choices[choice_idx]
            await _update_answer(state, data, question_id, selected_choice)
            await callback.message.edit_text(f"✅ Вы выбрали: {selected_choice}")
            
            if data['current_question'] < len(data['questions']) - 1:
                await handle_next_question_auto(callback.message, state)
            else:
                await handle_review(callback.message, state)
                
        await callback.answer()
    except Exception as e:
        logger.error(f"Choice error: {str(e)}")
        await handle_db_error(callback.message)


# --------------------------
#  Answer Editing
# --------------------------
@candidate_router.callback_query(F.data.startswith("edit_"), CandidateStates.review)
async def handle_edit_review(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[1])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer(msg_templates.QUESTION_NOT_FOUND)
                return

            data = await _get_current_interaction_data(state)
            new_current = data['questions'].index(question_id)
            
            await state.update_data(current_question=new_current)
            await state.set_state(CandidateStates.editing)
            
            edit_text = (
                f"✏️ Редактирование вопроса {new_current+1}:\n\n"
                f"{question.question_text}\n\n"
            )
            edit_text += (
                f"Текущий ответ: {data['answers'].get(str(question_id), 'Нет ответа')}"
            )
            
            is_choice_based_question = False
            if question.expected_format == AnswerFormat.CHOICE and question.choices:
                keyboard = _build_choice_keyboard(
                    question.choices, 
                    "edit_choice", 
                    "↩️ Назад к обзору",
                    is_editing=True
                )
                edit_text += ""
                is_choice_based_question = True
            else:
                edit_text += "\n\nОтправьте новый ответ:"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="↩️ Назад к обзору", callback_data="cancel_edit")]
                ])

            try:
                if is_choice_based_question:
                    await callback.message.edit_text(edit_text, reply_markup=keyboard)
                else:
                    await callback.message.answer(edit_text, reply_markup=keyboard)
            
            except Exception as edit_error:
                logger.warning(f'Could not edit message: {str(edit_error)}')
                await callback.message.answer(edit_text, reply_markup=keyboard)
            
            await callback.answer()
    except Exception as e:
        logger.error(f"Edit error: {str(e)}")
        await handle_db_error(callback.message)


@candidate_router.message(CandidateStates.editing)
async def handle_edit_answer(message: Message, state: FSMContext):
    '''Обработчик редактирования ответа кандидата'''
    try:
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
        await _update_last_active(
                candidate_id=data['candidate_id'], 
                application_id=data['application_id']
        )
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if question.expected_format == AnswerFormat.FILE and not message.document:
                await message.answer(msg_templates.FILE_EXPECTED)
                return
                
            answer_content = await _process_answer_content(message, question)
            if not answer_content:
                return

            await _update_answer(state, data, question_id, answer_content)
            await handle_review(message, state)
            await state.set_state(CandidateStates.review)

    except Exception as e:
        logger.error(f"Edit answer error: {str(e)}")
        await handle_db_error(message)


@candidate_router.callback_query(F.data.startswith("edit_choice_"))
async def handle_edit_choice(callback: CallbackQuery, state: FSMContext):
    '''Обработчик редактирования ответа на вопрос с вариантами ответа'''
    try:
        choice_idx = int(callback.data.split("_")[-1])
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question or not question.choices:
                await callback.answer("❌ Неверный вариант")
                return

            selected_choice = question.choices[choice_idx]
            await _update_answer(state, data, question_id, selected_choice)
            await handle_review(callback.message, state)
            await callback.answer()
    except Exception as e:
        logger.error(f"Edit choice error: {str(e)}")
        await handle_db_error(callback.message)


@candidate_router.callback_query(F.data == "cancel_edit", CandidateStates.editing)
async def handle_cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CandidateStates.review)
    await handle_review(callback.message, state)
    await callback.answer()


# --------------------------
#  Form Submission
# --------------------------
@candidate_router.callback_query(F.data == "submit_answers", CandidateStates.review)
async def handle_submission(callback: CallbackQuery, state: FSMContext):
    '''Обработчик отправки заполненной формы'''
    try:
        data = await _get_current_interaction_data(state)
        
        with Session() as db:
            application = db.query(Application).get(data['application_id'])
            if application.status != ApplicationStatus.ACTIVE:
                await callback.answer(msg_templates.FORM_ALREADY_SUBMITTED)
                return

            application.status = ApplicationStatus.REVIEW
            interaction = db.query(BotInteraction).filter_by(
                application_id=data['application_id']
            ).first()
            interaction.state = InteractionState.COMPLETED
            interaction.completed_at = datetime.utcnow()
                 
            db.commit()
 
        await callback.message.answer(msg_templates.ON_FORM_SUBMIT)
        
        vacancy_id=data.get('vacancy_id', -1)
        application_id=data.get('application_id', -1),
        # Собираем ответы кандидата
        formatted_answers = build_json(
            application_id=application_id,
            vacancy_id=vacancy_id
        )
        # Отправляем запросы в GigaChat
        await handle_proceed_to_llm(
            candidate_id=data.get('candidate_id', -1),
            application_id=application_id,
            vacancy_id=vacancy_id,
            answers=formatted_answers
        )
        
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Submit error: {str(e)}")
        await handle_db_error(callback.message, "Ошибка отправки анкеты")


# --------------------------
#  Handle LLM request
# --------------------------
async def handle_proceed_to_llm(
    candidate_id: int,
    application_id: int,
    vacancy_id: int,
    answers: str
):
    '''Отправить ответы кандидата в GigaChat и уведомить о результатах HR-специалистов'''
    # Инициализируем скрининг с Telegam бота
    tg_screening = TelegramScreening()
    # Отправляем ответы кандидата на оценку в GigaChat
    telegram_screening_score = await tg_screening.screen_answers(answers)
    try:
        analysis_score = int(telegram_screening_score)
    except (ValueError, TypeError):
        telegram_screening_score = 0
        
    try:
        with Session() as db:
            # Сохраняем результаты обработки нейросетью
            analysis_result = AnalysisResult(
                candidate_id=candidate_id,
                application_id=application_id,
                gigachat_score=telegram_screening_score,
                # TODO:
                # - Решение должно зависеть от оценки GigaChat
                final_decision="В РАЗРАБОТКЕ" if analysis_score > 8 else "В РАЗРАБОТКЕ",
                processed_at=datetime.now(timezone.utc)
            )
            db.add(analysis_result)
            db.flush()
            
            decision = analysis_result.final_decision
            
            # Создаем уведомления для HR
            notification = HrNotification(
                candidate_id=candidate_id,
                application_id=application_id,
                vacancy_id=vacancy_id,
                analysis_score=analysis_score,
                final_decision=decision,           
                status="new",
                sent_at=datetime.now(timezone.utc)
            )
            db.add(notification)
            
            db.commit()
            
    except Exception as e:
        logger.error(f'Error occured in handle_proceed_to_llm: {str(e)}')
        raise
        

# --------------------------
#  Handle NO-OP
# --------------------------
@candidate_router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    '''
        Пустая операция
        Используется для CallbackQuery которые не требуют обработки
        Например: кнопка с текущей страницей в меню пагинации
    '''
    await callback.answer()