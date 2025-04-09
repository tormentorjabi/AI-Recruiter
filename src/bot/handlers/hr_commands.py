from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from src.database.session import Session
from src.database.models import HrSpecialist


hr_commands_router = Router()

class ToggleWorkModeStates(StatesGroup):
    waiting_for_confirmation = State()

@hr_commands_router.message(Command('change_work_mode'))
async def toggle_work_mode(
    message: Message,
    state: FSMContext
):
    with Session() as db:
        hr = db.query(HrSpecialist).filter_by(
            telegram_id=str(message.from_user.id),
            is_approved=True
        ).first()

        if not hr:
            await message.answer(
                "❌ Вы не зарегистрированы как HR-специалист.\n"
                "Если вы желаете зарегистрироваться как HR, запросите "
                "токен регистрации у вашего администратора и выполните "
                "команду /register_hr"
            )
            return
        
        hr_work_mode = hr.work_mode
        
        await state.update_data(hr_id=hr.id)
        await message.answer(
                "Режим получения уведомлений:\n"
                f"{'✅ Активен' if hr_work_mode else '❌ Не активен'}\n\n"
                "Хотите сменить режим?\n"
                "Введите [Да/Нет] для подтверждения:"
            )
        await state.set_state(ToggleWorkModeStates.waiting_for_confirmation)
        

@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation),
    F.text.casefold().in_({"да", "yes", "д", "y"})
)
async def confirm_change_work_mode(message: Message, state: FSMContext):
    data = await state.get_data()
    
    with Session() as db:
        hr = db.query(HrSpecialist).get(data['hr_id'])
    
        if not hr:
            await message.answer("❌ HR-специалист не найден в базе данных")
            await state.clear()
            return

        new_status = not hr.work_mode
        hr.work_mode = new_status
        db.commit()

        status_text = "Активен" if new_status else "Не активен"
        await message.answer(
            f"🆕 Режим работы изменен на: `{status_text}`\n"
            f"Уведомления о кандидатах: {'✅ Включены' if new_status else '❌ Выключены'}",
            parse_mode="Markdown"
        )
    
    await state.clear()
    

@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation)
)
async def cancel_change_work_mode(message: Message, state: FSMContext):
    await message.answer("❌ Изменение режима работы отменено пользователем")
    await state.clear()
