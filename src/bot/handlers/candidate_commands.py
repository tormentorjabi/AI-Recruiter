import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import and_
from datetime import datetime, timedelta

from src.database.session import Session
from src.database.models import (
    Candidate,
    Application,
    BotQuestion,
    HrNotification,
    Vacancy,
    BotInteraction,
    HrSpecialist
)

from src.database.models.application import ApplicationStatus
from src.database.models.bot_interaction import InteractionState
from src.database.models.bot_question import AnswerFormat

logger = logging.getLogger(__name__)
candidate_router = Router()

class CandidateStates(StatesGroup):
    answering = State()
    review = State()
    editing = State()


# --------------------------
#  Utils
# --------------------------
async def _show_question(question: BotQuestion, message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_num = data['current_question'] + 1
        total = len(data['questions'])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Следующий вопрос", callback_data="next_question")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_process")]
        ])
        
        await message.answer(
            f"Вопрос {current_num}/{total}:\n\n{question.question_text}",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error showing question: {str(e)}")
        raise


async def _handle_db_error(message: Message, error_msg: str = "Произошла ошибка"):
    """Handle database errors consistently"""
    await message.answer(f"⚠️ {error_msg}. Попробуйте позже.")
    logger.error(error_msg)


async def handle_review(message: Message, state: FSMContext):
    '''Финальная сводка по ответам кандидата'''
    try:
        data = await state.get_data()
        
        with Session() as db:
            questions = db.query(BotQuestion).filter(
                BotQuestion.id.in_(data['questions'])
            ).order_by(BotQuestion.order).all()
            
            answers = []
            for idx, q in enumerate(questions):
                answer = data['answers'].get(str(q.id), '❌ Нет ответа')
                if q.expected_format == AnswerFormat.FILE and answer.startswith("FILE:"):
                    answer = "📎 Прикрепленный файл"
                answers.append(f"{idx+1}. {q.question_text}\nОтвет: {answer}")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"✏️ Вопрос {idx+1}", callback_data=f"edit_{q.id}")]
                for idx, q in enumerate(questions)
            ] + [
                [InlineKeyboardButton(text="✅ Подтвердить отправку", callback_data="submit_answers")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_process")]
            ])
            
            await message.answer(
                "📝 Ваши ответы:\n\n" + "\n\n".join(answers),
                reply_markup=keyboard
            )
            await state.set_state(CandidateStates.review)
            
    except Exception as e:
        logger.error(f"Error generating review: {str(e)}")
        await _handle_db_error(message)


async def handle_next_question_auto(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_idx = data['current_question']
        
        with Session() as db:
            next_question_id = data['questions'][current_idx + 1]
            next_question = db.query(BotQuestion).get(next_question_id)
            
            await state.update_data(current_question=current_idx + 1)
            await _show_question(next_question, message, state)
            
    except Exception as e:
        logger.error(f"Auto next question error: {str(e)}")
        await _handle_db_error(message)


# --------------------------
#  Initialize dialog and cancel dialog commands
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
            "❌ Процесс прохождения отменен. "
            "Для возобновления используйте /start"
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
            # Security check and candidate validation
            candidate = db.query(Candidate).filter(
                Candidate.telegram_id == telegram_id
            ).first()
            
            if not candidate:
                await message.answer("⚠️ Вы не зарегистрированы как соискатель")
                return

            # Validate active application
            application = db.query(Application).filter(
                and_(
                    Application.candidate_id == candidate.id,
                    Application.status == ApplicationStatus.ACTIVE
                )
            ).join(Vacancy).first()
            
            if not application:
                await message.answer(
                    "❌ Нет активных откликов по вакансиям, "
                    "которые нуждались бы в прохождении опроса.\n\n"
                    "Если вы недавно заполняли форму, "
                    "пожалуйста, дождитесь нашего ответа!"
                )
                return

            interaction = db.query(BotInteraction).filter(
                BotInteraction.application_id == application.id
            ).first()
            
            questions = db.query(BotQuestion).filter(
                BotQuestion.vacancy_id == application.vacancy_id
            ).order_by(BotQuestion.order).all()
            
            if not questions:
                await message.answer("⚠️ Для вакансии нет вопросов")
                return

            if interaction and interaction.state == InteractionState.PAUSED:
                # Ответы кандидата хранятся 12 часов, затем форму нужно заполнять с начала
                if (datetime.utcnow() - interaction.last_active) > timedelta(hours=12):
                    db.delete(interaction)
                    db.commit()
                    await message.answer("❌ Сессия истекла, начните заново")
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
                        (i for i, qid in enumerate([q.id for q in questions]) 
                        if qid == interaction.current_question_id), 0
                    )
                }
                resume_question = questions[state_data['current_question']]
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
                    'current_question': 0
                }
                resume_question = questions[0]
            
            db.commit()
            await state.set_data(state_data)
            
            # TODO:
            # Вывести все сбщ такого плана в шаблонки, вместе с вопросами
            # для GigaChat
            await message.answer(
                f"Приветствуем вас, {candidate.full_name}!\n\n"
                f"В рамках вашего отклика по вакансии: `{application.vacancy.title}` "
                f"вам необходимо пройти опрос, состоящий из `{len(questions)} вопросов`.\n"
                "Без прохождения данного опроса, мы не сможем вынести окончательное решение "
                "по вашей кандидатуре.\n\n"
                "Перед отправкой анкеты, вы сможете увидеть все ответы, данные вами, "
                "а также при необходимости изменить каждый из них.\n\n"
                "Вы не ограничены по времени\n"
                "Вы в любой момент можете прервать сессию прохождения опроса\n\n"
                "Удачи 👍🏻",
                parse_mode="Markdown"
            )
            await _show_question(resume_question, message, state)
            await state.set_state(CandidateStates.answering)

    except Exception as e:
        logger.error(f"Start error: {str(e)}")
        await _handle_db_error(message)


# --------------------------
#  Candidate answers handlers
# --------------------------
@candidate_router.callback_query(F.data == "next_question", CandidateStates.answering)
async def handle_next_question(callback: CallbackQuery, state: FSMContext):
    '''Переход к следующему вопросу'''
    try:
        data = await state.get_data()
        current_idx = data['current_question']
        questions = data['questions']

        if current_idx >= len(questions) - 1:
            # Вопросы закончились, идём к сводке
            return await handle_review(callback.message, state)

        with Session() as db:
            next_question_id = questions[current_idx + 1]
            next_question = db.query(BotQuestion).get(next_question_id)
            
            interaction = db.query(BotInteraction).filter_by(
                application_id=data['application_id']
            ).first()
            
            if interaction:
                interaction.current_question_id = next_question_id
                interaction.last_active = datetime.utcnow()
                db.commit()

            await state.update_data(current_question=current_idx + 1)
            await _show_question(next_question, callback.message, state)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Next question error: {str(e)}")
        await _handle_db_error(callback.message)


@candidate_router.message(CandidateStates.answering)
async def handle_text_answer(message: Message, state: FSMContext):
    '''Обработка ответа кандидата'''
    try:
        data = await state.get_data()
        current_idx = data['current_question']
        question_id = data['questions'][current_idx]
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await message.answer("❌ Вопрос не найден")
                return

            if question.expected_format == AnswerFormat.FILE:
                await message.answer("❌ Ожидается файл")
                return
                
            if question.expected_format == AnswerFormat.CHOICE:
                if message.text not in (question.choices or []):
                    await message.answer(f"❌ Выберите: {', '.join(question.choices)}")
                    return

            # Обновляем записи об ответах кандидата
            new_answers = {**data['answers'], str(question_id): message.text}
            await state.update_data(answers=new_answers)
            
            interaction = db.query(BotInteraction).filter_by(
                application_id=data['application_id']
            ).first()
            
            if interaction:
                interaction.answers = new_answers
                interaction.last_active = datetime.utcnow()
                db.commit()

            await message.answer(f"✅ Ответ сохранен: {message.text}")
            
            if await state.get_state() == CandidateStates.editing:
                await handle_review(message, state)
                await state.set_state(CandidateStates.review)
            elif current_idx < len(data['questions']) - 1:
                await handle_next_question_auto(message, state)
            else:
                await handle_review(message, state)

    except Exception as e:
        logger.error(f"Answer handling error: {str(e)}")
        await _handle_db_error(message)


# --------------------------
#  Answer's review and editing handlers
# --------------------------
@candidate_router.callback_query(F.data.startswith("edit_"), CandidateStates.review)
async def handle_edit_review(callback: CallbackQuery, state: FSMContext):
    try:
        question_id = int(callback.data.split("_")[1])
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            if not question:
                await callback.answer("❌ Вопрос не найден")
                return

            data = await state.get_data()
            new_current = data['questions'].index(question_id)
            
            await state.update_data(current_question=new_current)
            await state.set_state(CandidateStates.editing)
            
            await callback.message.answer(
                f"✏️ Редактирование вопроса {new_current+1}:\n\n"
                f"{question.question_text}\n\n"
                f"Текущий ответ: {data['answers'].get(str(question_id), '❌ Нет ответа')}\n\n"
                "Отправьте новый ответ:"
            )
            await callback.answer()
    except Exception as e:
        logger.error(f"Edit review error: {str(e)}")
        await _handle_db_error(callback.message)


@candidate_router.message(CandidateStates.editing)
async def handle_edit_answer(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_idx = data['current_question']
        question_id = data['questions'][current_idx]
        
        with Session() as db:
            question = db.query(BotQuestion).get(question_id)
            
            if question.expected_format == AnswerFormat.FILE and not message.document:
                await message.answer("❌ Ожидается файл")
                return
                
            if question.expected_format == AnswerFormat.CHOICE:
                if message.text not in (question.choices or []):
                    await message.answer(f"❌ Выберите: {', '.join(question.choices)}")
                    return

            new_answer = message.document.file_id if message.document else message.text
            new_answers = {**data['answers'], str(question_id): new_answer}
            
            await state.update_data(answers=new_answers)
            
            interaction = db.query(BotInteraction).filter_by(
                application_id=data['application_id']
            ).first()
            
            if interaction:
                interaction.answers = new_answers
                interaction.last_active = datetime.utcnow()
                db.commit()

            await message.answer("✅ Ответ успешно обновлен!")
            await handle_review(message, state)
            await state.set_state(CandidateStates.review)

    except Exception as e:
        logger.error(f"Edit answer error: {str(e)}")
        await _handle_db_error(message)
        

@candidate_router.callback_query(F.data == "cancel_edit", CandidateStates.editing)
async def handle_cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CandidateStates.review)
    await handle_review(callback.message, state)
    await callback.answer()


# --------------------------
#  Form submit handlers
# --------------------------
@candidate_router.callback_query(F.data == "submit_answers", CandidateStates.review)
async def handle_submission(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        
        with Session() as db:
            application = db.query(Application).get(data['application_id'])
            if application.status != ApplicationStatus.ACTIVE:
                await callback.answer("⚠️ Вы уже отправили эту анкету")
                return

            application.status = ApplicationStatus.REVIEW
            
            interaction = db.query(BotInteraction).filter_by(
                application_id=data['application_id']
            ).first()
            interaction.state = InteractionState.COMPLETED
            interaction.completed_at = datetime.utcnow()
            
            # TODO: 
            # Add GigaChat logic
            # Correct bot_interaction db records
            # Add candidate_answer?
            # Add real notifications
            hr_specialists = db.query(HrSpecialist).all()
            
            for hr in hr_specialists:
                notification = HrNotification(
                    candidate_id=data['candidate_id'],
                    hr_specialist_id=hr.id,
                    channel='Telegram',
                    sent_data={
                        "candidate": f"{data['candidate_name']}",
                        "vacancy": f"{data['vacancy_title']}",
                        "answers": len(data['answers'])
                    },
                    status="new"
                )
                db.add(notification)
            
            db.commit()

        await callback.message.answer(
            "✅ Анкета успешно отправлена! Мы свяжемся с вами по результатам."
        )
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Submission error: {str(e)}")
        await _handle_db_error(callback.message, "Ошибка отправки анкеты")
        