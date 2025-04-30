import secrets
import logging

from sqlalchemy.orm import Session as SqlAlchemySession
from datetime import datetime, timedelta, timezone

from src.database.session import Session
from src.database.models import Application

logger = logging.getLogger(__name__)


def generate_application_token(nbytes: int = 32) -> str:
    '''
    Сгенерировать токен для идентификации отклика.
    Используется secrets.token_urlsafe(nbytes)
    
    Args:
        nbytes (int): Количество рандомных байтов (default=32)
    
    Returns:
        token (str): Рандомная, URL-безопасная строка, в кодировке Base64
    '''
    return secrets.token_urlsafe(nbytes=nbytes)


def set_application_token(
    db: SqlAlchemySession,
    application_id: int,
    nbytes: int = 32,
    expiry_days: int = 31
) -> str:
    '''
    Сгенерировать и установить токен идентификации для записи конкретного отклика
    
    Args:
        db (SqlAlchemySession): Открытая сессия БД
        application_id (int): ID отклика в БД
        nbytes (int): Количество рандомных байтов (default=32),
        expiry_days (int): Срок жизни токена идентификации в днях (default=31)
    
    Returns:
        token (str): Рандомная, URL-безопасная строка, в кодировке Base64
    '''
    try:
        application = db.query(Application).get(application_id)
        if not application:
            return None
        
        while True:
            token = generate_application_token(nbytes=nbytes)
            
            if not db.query(Application).filter_by(auth_token=token).first():
                break
        
        application.auth_token = token
        application.token_expiry = datetime.now(timezone.utc) + timedelta(days=expiry_days)
        db.flush()
        
        return token
            
    except Exception as e:
        logger.error(f'Error in set_application_token: {str(e)}')
        return None