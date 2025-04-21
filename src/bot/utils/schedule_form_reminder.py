import asyncio
import logging
import src.bot.utils.message_templates as msg_templates

from aiogram import Bot

from src.database.session import Session
from src.database.models import BotInteraction
from src.database.models.bot_interaction import InteractionState


logger = logging.getLogger(__name__)


active_reminders = {}

async def schedule_form_reminder(
    bot: Bot,
    user_id: int,
    application_id: int,
    delay_seconds: int = 1800
):
    '''
    Запланировать напоминание для пользователя, который прекратил заполнение анкеты кандидата
    
    Args:
        bot (Bot): Экземпляр бота, для отправки сообщения
        user_id (int): Telegram ID пользователя, получателя напоминания
        application_id (int): ID отклика, по которому происходило заполнение анкеты
        delay_seconds (int): Время ожидания (в секундах) для отправки напоминания (default: 30 минут) 
    '''
    # Отменяем все существующие напоминания для данного пользователя
    if user_id in active_reminders:
        active_reminders[user_id].cancel()
    
    # Создаем новое напоминание         
    async def send_reminder():
        try:
            await asyncio.sleep(delay=delay_seconds)
            
            with Session() as db:
                interaction = db.query(BotInteraction).filter_by(
                    application_id=application_id
                ).first()
                
                # Отправлять напоминание будем только для приостановивших прохождение кандидатов
                if interaction and interaction.state == InteractionState.PAUSED:
                    await bot.send_message(
                        chat_id=user_id,
                        text=msg_templates.CANDIDATE_FORM_REMINDER,
                        parse_mode="Markdown"
                    )
                    logger.info(f'Sent form reminder to candidate {user_id} for application {application_id}')
        except Exception as e:
            logger.error(f'Error sending reminder: {str(e)}')
        finally:
            if user_id in active_reminders:
                del active_reminders[user_id]
    
    # Создаем запись о напоминании                
    reminder_task = asyncio.create_task(send_reminder())
    active_reminders[user_id] = reminder_task
    
    logger.info(f'Scheduled form reminder for user {user_id} in {delay_seconds} seconds')