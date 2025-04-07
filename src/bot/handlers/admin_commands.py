from aiogram import F
from aiogram import types, Router
from aiogram.filters import Command
from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID


admin_router = Router()


@admin_router.message(
    Command('generate_token'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def generate_token(message: types.Message):
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
    Command('list_HR'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def get_hr_list(message: types.Message):
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
                f"✅ В системе нет зарегистрированных HR-специалистов\n\n"
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
