from aiogram import F
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID


admin_router = Router()


class DeleteHRStates(StatesGroup):
    waiting_for_confirmation = State()


@admin_router.message(
    Command('generate_token'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def generate_token(message: Message):
    # By applying magic_filter F.chat.id == ADMIN_CHANNEL_ID
    # user outside of admin channel cannot access this command.
    # Thus, user warning message is not really needed.
    if message.chat.id != ADMIN_CHANNEL_ID:
        await message.answer(
            f"Вызов команды из этого чата недоступен",
        )
        return
    
    await message.answer(
        f"Запрос получен, ожидайте\n",
        parse_mode="Markdown"
    )
    
    with Session() as db:
        admin = db.query(HrSpecialist).filter_by(
            telegram_id=str(ADMIN_USER_ID)
        ).first()
        
        if not admin:
            admin = HrSpecialist(
                telegram_id=str(ADMIN_USER_ID),
                full_name="System Admin",
                is_approved=True
            )
            db.add(admin)
            db.commit()
    
        token = RegistrationToken.generate_token(admin.id)
        generate_token = token.token
        
        db.add(token)
        db.commit()
    
    await message.answer(
        f"Токен для регистрации HR-специалиста (активен 24ч):\n"
        f"`{generate_token}`",
        parse_mode="Markdown"
    )


@admin_router.message(
    Command('list_hr'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def get_hr_list(message: Message):
    if message.chat.id != ADMIN_CHANNEL_ID:
        await message.answer(
            f"Вызов команды из этого чата недоступен",
        )
        return
    
    with Session() as db:
        hrs = db.query(HrSpecialist).filter_by(
                is_approved=True
            ).order_by(HrSpecialist.created_at.desc()).all()
        
        if not hrs:
            await message.answer(
                f"❌ В системе нет зарегистрированных HR-специалистов\n\n"
                f"Для регистрации, воспользуйтесь командами создания токенов "
                f"и раздайте их сотрудникам!"
            )
            return
            
        response = "Список зарегистрированных HR-специалистов:\n\n"
        for hr in hrs:
            response += (
                f"• {hr.full_name}\n"
                f"  ID: `{hr.telegram_id}`\n"
                f"  Дата регистрации: {hr.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"    
            )
        
        await message.answer(response, parse_mode="Markdown")
        

@admin_router.message(
    Command('delete_hr'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def delete_hr(
    message: Message,
    state: FSMContext
):
    if message.chat.id != ADMIN_CHANNEL_ID:
        await message.answer(
            f"Вызов команды из этого чата недоступен",
        )
        return
    
    args = message.text.split(maxsplit=1)[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        await message.answer(
            "❌ Использование: /delete_hr <Telegram ID HR-специалиста>\n"
            "Пример: /delete_hr 123456789"
        )
        return

    telegram_id = args[0].strip()

    if telegram_id == str(ADMIN_USER_ID):
        await message.answer(
            "❌ Предотвращено удаление системного администратора"
        )
        return
    
    with Session() as db:
        hr = db.query(HrSpecialist).filter_by(
                is_approved=True,
                telegram_id=telegram_id
            ).first()
        
        if not hr:
            await message.answer(
                f"❌ HR-специалист с ID `{telegram_id}` не найден\n",
                parse_mode="Markdown"
            )
            await message.answer(
                f"Найти ID необходимого сотрудника можно с помощью комманды: "
                f"/list_hr"
            )
            return
        
        await state.update_data(hr_id=hr.id, telegram_id=telegram_id)
        await message.answer(
            f"⚠️ Вы уверены, что хотите удалить HR-специалиста:\n"
            f"Имя: {hr.full_name}\n"
            f"ID: {telegram_id}\n\n"
            "Введите [Да/Нет] для подтверждения:"
        )
        await state.set_state(DeleteHRStates.waiting_for_confirmation)


@admin_router.message(
    DeleteHRStates.waiting_for_confirmation,
    F.text.casefold().in_({"да", "yes", "д", "y"})
)
async def confirm_delete(message: Message, state: FSMContext):
    data = await state.get_data()

    with Session() as db:
        hr = db.query(HrSpecialist).get(data['hr_id'])

        if not hr:
            await message.answer("❌ HR-специалист не найден в базе данных")
            await state.clear()
            return

        db.query(RegistrationToken).filter_by(used_by=hr.id).delete()
        db.delete(hr)
        db.commit()

        await message.answer(
            f"✅ HR-специалист {hr.full_name} (ID: {data['telegram_id']}) удален",
            parse_mode="Markdown"
        )

    await state.clear()


@admin_router.message(
    DeleteHRStates.waiting_for_confirmation
)
async def cancel_delete(message: Message, state: FSMContext):
    await message.answer("❌ Удаление отменено пользователем")
    await state.clear()
