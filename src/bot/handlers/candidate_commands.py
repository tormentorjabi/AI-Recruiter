from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database.session import Session
from src.database.models import (
    HrSpecialist,
    Candidate,
    Application,
    BotQuestion,
    CandidateAnswer,
    Vacancy,
    BotInteraction
)


candidate_router = Router()

class CandidateStates(StatesGroup):
    answering = State()
    review = State()
    editing = State()


@candidate_router.message(Command('cancel'))
@candidate_router.callback_query(F.data == 'cancel_process')
async def cancel_interaction(
    query_or_msg: Message | CallbackQuery, 
    state: FSMContext
):
    if isinstance(query_or_msg, CallbackQuery):
        await query_or_msg.message.delete()
        message = query_or_msg.message
    else:
        message = query_or_msg

    data = await state.get_data()
    if data.get('current_question', 0) > 0:
        with Session() as db:
            interaction = db.query(BotInteraction).filter_by(
                candidate_id=data['candidate_id'],
                application_id=data['application_id']
            ).first()
            if interaction:
                interaction.current_state = 'paused'
                interaction.current_question = data['current_question']
                interaction.answers = data['answers']
                db.commit()

    await state.clear()
    await message.answer("❌ Процесс отменен. Для возобновления используйте /start")
    

@candidate_router.message(Command("start"))
async def candidate_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    
    with Session() as db:
        candidate = db.query(Candidate).filter_by(
            telegram_id=telegram_id
        ).first()
        if not candidate:
            await message.answer(
                "⚠️ Вы не зарегистрированы как соискатель "
                "по каким-либо вакансиям"
            )
            return
        
        application = db.query(Application).filter_by(
            candidate_id=candidate.id,
            status="active"
        ).join(Vacancy).first()
        
        if not application:
            await message.answer("❌ У вас нет активных откликов на вакансии")
            return
        
        interaction = db.query(BotInteraction).filter_by(
            candidate_id=candidate.id,
            application_id=application.id
        ).first()
        
        questions = db.query(BotQuestion).filter_by(
            vacancy_id=application.vacancy_id
        ).order_by(BotQuestion.order).all()
        
        if not questions:
            await message.answer("⚠️ Для этой вакансии пока нет вопросов")
            return
        
        vacancy = db.query(Vacancy).filter_by(
            id=application.vacancy_id
        ).first()
        
        await state.update_data(
            candidate_id=candidate.id,
            application_id=application.id,
            vacancy_id=application.vacancy_id,
            questions=[q.id for q in questions],
            answers={},
            current_question=0
        )
        
        questions_count = len(questions)
        first_question = questions[0]
        await message.answer(
                f"Приветствуем вас, {candidate.full_name}!\n\n"
                f"Для того, чтобы мы могли принять решение по вашей кандидатуре, "
                f"в рамках отклика на вакансию: `{vacancy.title}`, вам необходимо пройти опрос, "
                f"состоящий из {questions_count} вопросов.\n\n"
                "Вы можете отказаться от прохождения опроса в любой момент и вернуться к нему позже.",
                parse_mode="Markdown"
            )
        await message.answer(
            f"Вакансия: `{vacancy.title}`\n"
            f"Вопрос № 1 из {questions_count}:\n\n"
            f"{first_question.question_text}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отменить прохождение ❌", callback_data="cancel")]
            ]),
            parse_mode="Markdown"
        )
        await state.set_state(CandidateStates.answering)