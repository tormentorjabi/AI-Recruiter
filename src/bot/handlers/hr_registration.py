from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove

from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.config import ADMIN_CHANNEL_ID


registration_router = Router()

class HrRegistrationStates(StatesGroup):
    waiting_for_token = State()
    waiting_for_full_name = State()
    
    
@registration_router.message(Command('registerHR'))
async def start_hr_registration(message: Message, state: FSMContext):
    await message.answer(
        'Введите регистрационный токен, выданный администратором:',
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(HrRegistrationStates.waiting_for_token)
    
    
@registration_router.message(
    StateFilter(HrRegistrationStates.waiting_for_token),
    F.text.regexp(r'^[a-zA-Z0-9_-]{43}$')
)
async def process_token(message: Message, state: FSMContext):
    token_value = message.text.strip()
    
    with Session() as db:
        token = db.query(RegistrationToken).filter_by(
            token=token_value
        ).first()
        print(token)
        if not token:
            await message.answer("❌ Неверный или несуществующий токен")
            return await state.clear()
            
        if token.used_at:
            await message.answer(
                "❌ Данный токен уже был задействован. " +
                "Запросите новый токен у администратора системы")
            return await state.clear()
            
        if token.expires_at < datetime.utcnow():
            await message.answer("❌ Срок действия токена истек")
            return await state.clear()
            
        await state.update_data(token_id=token.id)
        await message.answer("Введите ваше полное имя (ФИО):")
        await state.set_state(HrRegistrationStates.waiting_for_full_name)
       
        
@registration_router.message(StateFilter(HrRegistrationStates.waiting_for_full_name))
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    user_data = await state.get_data()
    token_id = user_data['token_id']
    
    with Session() as db:
        token = db.query(RegistrationToken).get(token_id)
        
        if not token or token.used_at or token.expires_at < datetime.utcnow():
            await message.answer("❌ Срок действия токена истёк. Начните регистрацию заново.")
            return await state.clear()
        
        new_hr = HrSpecialist(
            telegram_id=str(message.from_user.id),
            full_name=full_name,
            is_approved=True
        )
        
        db.add(new_hr)
        db.flush()
        
        token.used_by = new_hr.id
        token.used_at = datetime.utcnow()
        
        db.commit()
        
        await message.answer(
            "✅ Регистрация успешно завершена!\n"
            f"Добро пожаловать, {new_hr.full_name}!\n"
            "Теперь вы будете получать уведомления о кандидатах."
        )
        
        await message.bot.send_message(
            ADMIN_CHANNEL_ID,
            f"🆕 Новый HR зарегистрирован: "
            f"[{new_hr.full_name}](tg://user?id={new_hr.telegram_id})\n"
            f"ID: `{new_hr.telegram_id}`",
            parse_mode="MarkdownV2"
        )
        
    await state.clear()
    