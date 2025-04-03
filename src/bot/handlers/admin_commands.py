from aiogram import types
from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.core.bot import dp
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID


@dp.message_handler(
    chat_id=ADMIN_CHANNEL_ID,
    user_id=ADMIN_USER_ID,
    commands=["generate_token"]
)
async def generate_token(message: types.Message):
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
    
    with Session() as db:
        db.add(token)
        db.commit()
    
    await message.answer(
        f"Токен для регистрации HR-специалиста (активен 24ч):\n"
        f"`{token.token}`",
        parse_mode="Markdown"
    )
