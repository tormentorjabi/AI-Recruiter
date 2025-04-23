import src.bot.utils.message_templates as msg_templates

from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.exc import IntegrityError

from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.config import ADMIN_CHANNEL_ID


hr_registration_router = Router()

class HrRegistrationStates(StatesGroup):
    waiting_for_token = State()
    waiting_for_full_name = State()
    
    
@hr_registration_router.message(Command('register_hr'))
async def start_hr_registration(message: Message, state: FSMContext):
    with Session() as db:
        existing_hr = db.query(HrSpecialist).filter_by(
            telegram_id=str(message.from_user.id)
        ).first()

        if existing_hr:
            await message.answer(msg_templates.HR_ALREADY_EXISTS)
            return

    await message.answer(
        msg_templates.INPUT_REGISTRATION_TOKEN,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(HrRegistrationStates.waiting_for_token)
    
    
@hr_registration_router.message(
    StateFilter(HrRegistrationStates.waiting_for_token),
    F.text.regexp(r'^[a-zA-Z0-9_-]{43}$')
)
async def process_token(message: Message, state: FSMContext):
    token_value = message.text.strip()
    
    with Session() as db:
        existing_hr = db.query(HrSpecialist).filter_by(
            telegram_id=str(message.from_user.id)
        ).first()

        if existing_hr:
            await message.answer(
                msg_templates.HR_ALREADY_EXISTS_WHILE_IN_REGISTRATION_PROCESS
            )
            await state.clear()
            return

        token = db.query(RegistrationToken).filter_by(
            token=token_value
        ).first()

        if not token:
            await message.answer(msg_templates.BAD_REGISTRATION_TOKEN)
            return await state.clear()
            
        if token.used_at:
            await message.answer(msg_templates.TOKEN_ALREADY_IN_USE)
            return await state.clear()
            
        if token.expires_at < datetime.utcnow():
            await message.answer(msg_templates.TOKEN_EXPIRED)
            return await state.clear()
            
        await state.update_data(token_id=token.id)
        await message.answer("Введите ваше полное имя (ФИО):")
        await state.set_state(HrRegistrationStates.waiting_for_full_name)
       
        
@hr_registration_router.message(StateFilter(HrRegistrationStates.waiting_for_full_name))
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    user_data = await state.get_data()
    token_id = user_data['token_id']
    
    hr_full_name = None
    hr_telegram_id = None

    try:
        with Session() as db:
            existing_hr = db.query(HrSpecialist).filter_by(
                telegram_id=str(message.from_user.id)
            ).first()
                
            if existing_hr:
                raise IntegrityError("Duplicate HR registration attempt")

            token = db.query(RegistrationToken).get(token_id)
            
            if not token or token.used_at or token.expires_at < datetime.utcnow():
                await message.answer(msg_templates.TOKEN_EXPIRED)
                return await state.clear()
            
            new_hr = HrSpecialist(
                telegram_id=str(message.from_user.id),
                full_name=full_name,
                is_approved=True,
                work_mode=True
            )
            
            db.add(new_hr)
            db.flush()
            
            hr_full_name = new_hr.full_name
            hr_telegram_id = new_hr.telegram_id

            token.used_by = new_hr.id
            token.used_at = datetime.utcnow()
            
            db.commit()
            
    except IntegrityError as e:
        await message.answer(msg_templates.HR_ALREADY_EXISTS)
        await state.clear()
        return
    
    await message.answer(
        msg_templates.hr_registered_message(hr_full_name=hr_full_name)
    )
            
    await message.bot.send_message(
        ADMIN_CHANNEL_ID,
        msg_templates.hr_registered_notification_message(
            hr_full_name=hr_full_name,
            telegram_id=hr_telegram_id
        ),
        parse_mode="MarkdownV2"
    )
            
    await state.clear()
