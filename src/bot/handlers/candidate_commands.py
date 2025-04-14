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


@candidate_router.message(Command("cancel"), StateFilter("*"))
async def cancel_interaction(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "❌ Процесс отменен. Для начала нового сеанса используйте /start"
    )
    

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
        ).order_by(Application.application_date.desc()).first()
        
        if not application:
            await message.answer("❌ У вас нет активных откликов на вакансии")
            return
        
        questions = db.query(BotQuestion).filter_by(
            vacancy_id=application.vacancy_id
        ).order_by(BotQuestion.order).all()
        
        if not questions:
            await message.answer("⚠️ Для этой вакансии пока нет вопросов")
            return
        
        vacancy = db.query(Vacancy).filter_by(
            vacancy_id=application.vacancy_id
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
                f"Приветствуем вас, {candidate.full_name}!"
                f"Для того, чтобы мы могли принять решение по вашей кандидатуре, "
                f"в рамках отклика на вакансию: '{vacancy.title}' вам необходимо пройти опрос, "
                f"состоящий из {questions_count}\n\n"
            )
        await message.answer(
            f"Вакансия: {vacancy.title}\n"
            f"Вопрос 1 из {questions_count}:\n"
            f"{first_question.question_text}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отменить прохождение ❌", callback_data="cancel")]
            ])
        )
        await state.set_state(CandidateStates.answering)