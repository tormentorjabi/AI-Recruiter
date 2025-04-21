import asyncio
import logging

from aiogram import Bot
from datetime import datetime, timedelta

from src.bot.utils.schedule_form_reminder import schedule_form_reminder

from src.database.session import Session
from src.database.models import BotInteraction, Candidate
from src.database.models.bot_interaction import InteractionState


logger = logging.getLogger(__name__)


async def check_abandoned_forms(bot: Bot, delay_minutes: int = 30):
    '''
    Периодическая проверка на неактивность анкет и отправка уведомлений
    '''
    INACTIVITY_THRESHOLD = timedelta(minutes=delay_minutes)
    
    while True:
        try:
            with Session() as db:
                # Ищем BotInteraction, которые все ещё активны, но не были обновлены долгое время
                threshold_time = datetime.utcnow() - INACTIVITY_THRESHOLD
                abandoned_interactions = db.query(BotInteraction).filter(
                    BotInteraction.state == InteractionState.STARTED,
                    BotInteraction.last_active < threshold_time
                ).all()
                
                for interaction in abandoned_interactions:
                    # Останавливаем сессию прохождения
                    interaction.state = InteractionState.PAUSED
                    db.commit()
                    
                    candidate = db.query(Candidate).filter_by(
                        id=interaction.candidate_id
                    ).first()
                    
                    if candidate and candidate.telegram_id:
                        user_id = int(candidate.telegram_id)
                        # Планируем напоминание
                        await schedule_form_reminder(
                            bot=bot,
                            user_id=user_id,
                            application_id=interaction.application_id,
                            delay_seconds=(60 * delay_minutes)   
                        )
        except Exception as e:
            logger.error(f'Error checking for abandoned forms: {str(e)}')
        
        # Проверяем анкеты каждые 15 минут 
        await asyncio.sleep(60 * 15)
    