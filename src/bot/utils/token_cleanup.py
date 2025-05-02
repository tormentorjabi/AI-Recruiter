from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.database.session import Session
from src.database.models import RegistrationToken
from datetime import datetime

scheduler = AsyncIOScheduler()

def cleanup_expired_tokens():
    """
    AsyncIOScheduler задача, на удаление из базы данных истекших токенов регистрации для HR-специалистов
    """
    with Session() as db:
        db.query(RegistrationToken).filter(
            RegistrationToken.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        

scheduler.add_job(cleanup_expired_tokens, 'interval', hours=1)
