import logging
import src.bot.utils.message_templates as msg_templates

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import and_
from datetime import datetime, timedelta

from src.database.session import Session
from src.database.models import (
    Candidate, Application, BotQuestion, HrNotification,
    Vacancy, BotInteraction, HrSpecialist
)

from src.database.models.application import ApplicationStatus
from src.database.models.bot_interaction import InteractionState
from src.database.models.bot_question import AnswerFormat

from src.gigachat_module.telegram_screening import TelegramScreening


logger = logging.getLogger(__name__)
candidate_router = Router()

class CandidateStates(StatesGroup):
    answering = State()
    review = State()
    editing = State()


# --------------------------
#  Core Utilities
# --------------------------
async def _handle_db_error(message: Message, error_msg: str = "Произошла ошибка"):
    await message.answer(f"⚠️ {error_msg}. Попробуйте позже.")
    logger.error(error_msg)


async def _get_current_interaction_data(state: FSMContext):
    data = await state.get_data()
    return {
        'candidate_id': data.get('candidate_id'),
        'application_id': data.get('application_id'),
        'current_question': data.get('current_question', 0),
        'questions': data.get('questions', []),
        'answers': data.get('answers', {})
    }


async def _update_interaction_state(application_id: int, state_data: dict):
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


async def _show_question(question: BotQuestion, message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_num = data['current_question'] + 1
        total = len(data['questions'])
        
        if question.expected_format == AnswerFormat.CHOICE and question.choices:
            await message.answer(
                f"Вопрос {current_num}/{total} (выберите вариант):\n\n{question.question_text}",
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
    review_content = []
    for idx, q in enumerate(questions):
        answer = answers.get(str(q.id), '❌ Нет ответа')
        if q.expected_format == AnswerFormat.FILE and answer.startswith("FILE:"):
            answer = "📎 Прикрепленный файл"
        review_content.append(f"{idx+1}. {q.question_text}\nОтвет: {answer}")
    return "\n\n".join(review_content)


async def handle_review(message: Message, state: FSMContext, page: int = 0):
    try:
        data = await state.get_data()
        QUESTIONS_PER_PAGE = 5
        
        with Session() as db:
            questions = db.query(BotQuestion).filter(
                BotQuestion.id.in_(data['questions'])
            ).order_by(BotQuestion.order).all()
            
            content = await _build_review_content(questions, data['answers'])
            page_questions = questions[page*QUESTIONS_PER_PAGE:(page+1)*QUESTIONS_PER_PAGE]
            total_pages = (len(questions) + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE
            
            keyboard = await _build_review_keyboard(page_questions, page, total_pages)
            
            if hasattr(message, 'message_id'):
                await message.edit_text(f"📝 Ваши ответы:\n\n{content}", reply_markup=keyboard)
            else:
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
        await _handle_db_error(message)


async def _build_review_keyboard(questions, current_page, total_pages):
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


# --------------------------
#  Common Handlers
# --------------------------
@candidate_router.message(Command('cancel'))
@candidate_router.callback_query(F.data == 'cancel_process')
async def cancel_interaction(query_or_msg: Message | CallbackQuery, state: FSMContext):
    '''Отменить прохождение опросника'''
    try:
        message = query_or_msg.message if isinstance(query_or_msg, CallbackQuery) else query_or_msg
        data = await state.get_data()
        
        if data.get('current_question', 0) > 0:
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
            except Exception as e:
                logger.error(f"Error saving paused state: {str(e)}")

        await state.clear()
        await message.answer(
            msg_templates.CANDIDATE_CANCELLED_FORM,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Cancel error: {str(e)}")
        await _handle_db_error(message)


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
                await message.answer(msg_templates.CANDIDATE_NOT_FOUND)
                await message.answer(msg_templates.NOT_REGISTERED_AS_HR)
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

            interaction = db.query(BotInteraction).filter(
                BotInteraction.application_id == application.id
            ).first()
            
            questions = db.query(BotQuestion).filter(
                BotQuestion.vacancy_id == application.vacancy_id
            ).order_by(BotQuestion.order).all()
            
            if not questions:
                await message.answer(
                    msg_templates.VACANCY_QUESTIONS_NOT_FOUND
                )
                return

            if interaction and interaction.state == InteractionState.PAUSED:
                # Ответы кандидата хранятся 12 часов, затем форму нужно заполнять с начала
                if (datetime.utcnow() - interaction.last_active) > timedelta(hours=12):
                    db.delete(interaction)
                    db.commit()
                    await message.answer(
                        msg_templates.CANDIDATE_BOT_INTERACTION_SESSION_TIMEOUT
                    )
                    return

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
                interaction.state = InteractionState.STARTED
                resume_question = questions[state_data['current_question']]
                await message.answer("🔄 Возобновляем ваше предыдущее заполнение формы")
            else:
                interaction = BotInteraction(
                    candidate_id=candidate.id,
                    application_id=application.id,
                    current_question_id=questions[0].id,
                    vacancy_id=application.vacancy_id,
                    state=InteractionState.STARTED
                )
                db.add(interaction)
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
            
            await message.answer(
                msg_templates.get_candidate_on_start_bot_interaction_message(
                    db_candidate_full_name=candidate.full_name,
                    vacancy_title=application.vacancy.title,
                    questions_length=len(questions)),
                parse_mode="Markdown"
            )
            await _show_question(resume_question, message, state)
            await state.set_state(CandidateStates.answering)

    except Exception as e:
        logger.error(f"Start error: {str(e)}")
        await _handle_db_error(message)


# --------------------------
#  Question Navigation
# --------------------------
@candidate_router.callback_query(F.data == "next_question", CandidateStates.answering)
async def handle_next_question(callback: CallbackQuery, state: FSMContext):
    try:
        data = await _get_current_interaction_data(state)
        
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
        await _handle_db_error(callback.message)


async def handle_next_question_auto(message: Message, state: FSMContext):
    try:
        data = await _get_current_interaction_data(state)
        with Session() as db:
            next_question = db.query(BotQuestion).get(data['questions'][data['current_question'] + 1])
            await state.update_data(current_question=data['current_question'] + 1)
            await _show_question(next_question, message, state)
    except Exception as e:
        logger.error(f"Auto next error: {str(e)}")
        await _handle_db_error(message)


@candidate_router.callback_query(F.data.startswith("review_page_"))
async def handle_review_pagination(callback: CallbackQuery, state: FSMContext):
    '''Обработка нумерации на просмотре ответов'''
    try:
        page = int(callback.data.split("_")[-1])
        await handle_review(callback.message, state, page)
        await callback.answer()
    except Exception as e:
        logger.error(f"Pagination error: {str(e)}")
        await _handle_db_error(callback.message)


# --------------------------
#  Answer Handling
# --------------------------
@candidate_router.message(CandidateStates.answering)
async def handle_text_answer(message: Message, state: FSMContext):
    try:
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
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
                await handle_review(message, state)
                await state.set_state(CandidateStates.review)
            elif data['current_question'] < len(data['questions']) - 1:
                await handle_next_question_auto(message, state)
            else:
                await handle_review(message, state)

    except Exception as e:
        logger.error(f"Answer error: {str(e)}")
        await _handle_db_error(message)


async def _process_answer_content(message: Message, question: BotQuestion):
    if question.expected_format == AnswerFormat.FILE:
        if not message.document:
            await message.answer(msg_templates.FILE_EXPECTED)
            return None
        return f"FILE:{message.document.file_id}"
    return message.text


async def _update_answer(state: FSMContext, data: dict, question_id: int, answer: str):
    new_answers = {**data['answers'], str(question_id): answer}
    await state.update_data(answers=new_answers)
    await _update_interaction_state(data['application_id'], {
        **data,
        'answers': new_answers
    })


@candidate_router.callback_query(F.data.startswith("choice_"))
async def handle_choice_answer(callback: CallbackQuery, state: FSMContext):
    try:
        choice_idx = int(callback.data.split("_")[1])
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
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
        await _handle_db_error(callback.message)


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
            
            if question.expected_format == AnswerFormat.CHOICE and question.choices:
                keyboard = _build_choice_keyboard(
                    question.choices, 
                    "edit_choice", 
                    "↩️ Назад к обзору",
                    is_editing=True
                )
                await callback.message.edit_text(
                    f"✏️ Редактирование вопроса {new_current+1}:\n\n"
                    f"{question.question_text}\n\n"
                    f"Текущий ответ: {data['answers'].get(str(question_id), '❌ Нет ответа')}",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    f"✏️ Редактирование вопроса {new_current+1}:\n\n"
                    f"{question.question_text}\n\n"
                    f"Текущий ответ: {data['answers'].get(str(question_id), '❌ Нет ответа')}\n\n"
                    "Отправьте новый ответ:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="↩️ Назад к обзору", callback_data="cancel_edit")]
                    ])
                )
            await callback.answer()
    except Exception as e:
        logger.error(f"Edit error: {str(e)}")
        await _handle_db_error(callback.message)


@candidate_router.message(CandidateStates.editing)
async def handle_edit_answer(message: Message, state: FSMContext):
    try:
        data = await _get_current_interaction_data(state)
        question_id = data['questions'][data['current_question']]
        
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
        await _handle_db_error(message)


@candidate_router.callback_query(F.data.startswith("edit_choice_"))
async def handle_edit_choice(callback: CallbackQuery, state: FSMContext):
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
        await _handle_db_error(callback.message)


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
            
            for hr in db.query(HrSpecialist).all():
                notification = HrNotification(
                    candidate_id=data['candidate_id'],
                    hr_specialist_id=hr.id,
                    channel='Telegram',
                    sent_data={
                        "candidate": data.get('candidate_name', ''),
                        "vacancy": data.get('vacancy_title', ''),
                        "answers": data['answers']
                    },
                    status="new"
                )
                db.add(notification)
            
            db.commit()

        await callback.message.answer(msg_templates.ON_FORM_SUBMIT)
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Submit error: {str(e)}")
        await _handle_db_error(callback.message, "Ошибка отправки анкеты")

@candidate_router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()