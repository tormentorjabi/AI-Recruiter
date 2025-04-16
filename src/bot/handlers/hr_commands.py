import src.bot.utils.message_templates as msg_templates

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
            await message.answer(msg_templates.NOT_REGISTERED_AS_HR)
            return
        
        hr_work_mode = hr.work_mode
        
        await state.update_data(hr_id=hr.id)
        await message.answer(
                msg_templates.confirm_change_work_mode_message(work_mode=hr_work_mode),
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
            await message.answer(msg_templates.HR_NOT_FOUND_IN_DATABASE)
            await state.clear()
            return

        new_status = not hr.work_mode
        hr.work_mode = new_status
        db.commit()

        status_text = "Активен" if new_status else "Не активен"
        await message.answer(
           msg_templates.work_mode_changed_message(
               status_text=status_text,
               status=new_status
           ),
           parse_mode="Markdown"
        )
    
    await state.clear()
    

@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation)
)
async def cancel_change_work_mode(message: Message, state: FSMContext):
    await message.answer(msg_templates.WORK_MODE_CHANGE_CANCELLED)
    await state.clear()
