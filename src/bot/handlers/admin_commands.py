from aiogram import types, Router
from aiogram.filters import Command
from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID


admin_router = Router()


@admin_router.message(Command('generate_token'))
async def generate_token(message: types.Message):
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
