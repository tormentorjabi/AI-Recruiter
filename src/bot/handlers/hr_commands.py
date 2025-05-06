import logging
import src.bot.utils.message_templates as msg_templates
from src.gigachat_module.utils.formatters import candidate_answers_formatter

from aiogram import Bot
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardButton, InlineKeyboardMarkup
)
from datetime import datetime
from sqlalchemy import or_

from src.database.session import Session
from src.database.models import (
    HrSpecialist, HrNotification, Candidate, 
    Application, Vacancy, Resume
)

from src.bot.utils.bot_answers_json_builder import build_json
from src.bot.utils.error_handlers import handle_db_error


logger = logging.getLogger(__name__)
hr_commands_router = Router()

ACCEPT_DECISION = True
DECLINE_DECISION = False


# --------------------------
#  Display Helpers
# --------------------------
def get_status_display(status: str) -> str:
    """Convert status code to human-readable text"""
    status_map = {
        "new": "🆕 Доступен для обработки",
        "processing": "⏳ В обработке",
        # Статусы обработки HR'ом
        "approved": "✅ Одобрен",
        "declined": "❌ Отклонен",
        # Решения GigaChat'а
        "approve": "✅ Соответствует критериям",
        "reject": "❌ Ниже критериев"
    }
    return status_map.get(status, f"Неизвестный ({status})")


def _build_notifications_keyboard(notifications, source_menu: str, page: int = 0, items_per_page: int = 10):
    # Все решения сортируются по уменьшению оценки GigaChat
    with Session() as db:
        # Словарь типа: {application_id: gigachat_score (resume score)}
        resume_scores = {
            r.application_id: r.gigachat_score 
            for r in db.query(Resume).filter(
                Resume.application_id.in_(
                    [n.application_id for n in notifications if n.application_id]
                )
            ).all()
        }
    
    sorted_notifications = sorted(
        notifications,
        key=lambda notif: (
            {"processing": 0, "new": 1, "approved": 2, "declined": 3}.get(notif.status, 4),
            # Объединенная оценка по резюме + по ответам
            -((notif.analysis_score or 0) * 1 + (resume_scores.get(notif.application_id, 0) * 1))
            )
    )

    total_pages = (len(sorted_notifications) + items_per_page - 1) // items_per_page
    page_notifications = sorted_notifications[page*items_per_page:(page+1)*items_per_page]
    
    keyboard = []
    with Session() as db:
        for notification in page_notifications:
            vacancy = db.query(Vacancy).get(notification.vacancy_id)
            resume_score = resume_scores.get(notification.application_id, 0)
            vacancy_title = vacancy.title
            btn_text = (
                f"{vacancy_title[:15]} | "
                f"Оценка: {notification.analysis_score + resume_score} | "
                f"{get_status_display(notification.status)}"
            )
            keyboard.append([
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"notification_detail_{notification.id}_{source_menu}"
                )
            ])
    
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(
                text="◀️", 
                callback_data=f"notifications_page_{source_menu}_{page-1}"
            ))
        pagination.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", 
            callback_data="noop"
        ))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(
                text="▶️", 
                callback_data=f"notifications_page_{source_menu}_{page+1}"
            ))
        keyboard.append(pagination)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _get_archive_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=msg_templates.REVIEW_APPROVED, 
                callback_data="get_notifications_a_approved")],
            [InlineKeyboardButton(
                text=msg_templates.REVIEW_DECLINED, 
                callback_data="get_notifications_a_declined")],
            [InlineKeyboardButton(
                text=msg_templates.BACK_TO_LIST, 
                callback_data="back_to_main_menu")]
        ]) 
    return keyboard

   
# --------------------------
#  Init Commands Handlers
# --------------------------
'''
    TODO:
        - /get_archive - показать архив (двойной - approved/declined)
'''
@hr_commands_router.message(Command("get_reviews"))
async def _get_reviews_selection(message: Message, user=None):
    '''Сформировать меню с выбором категории решений'''
    try:
        with Session() as db:
            user_id = user.id if user else message.from_user.id
            
            hr = db.query(HrSpecialist).filter_by(
                telegram_id=str(user_id),
                is_approved=True
            ).first()

            if not hr:
                await message.answer(
                    msg_templates.NOT_REGISTERED_AS_HR,
                    parse_mode="Markdown"
                )
                return
            
            all_notifications = db.query(HrNotification).all()
            
            if not all_notifications:
                await message.answer(msg_templates.EMPTY_REVIEWS)
                return
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=msg_templates.NEW_REVIEWS_BUTTON, 
                    callback_data="get_notifications_n")],
                [InlineKeyboardButton(
                    text=msg_templates.PROCESSING_REVIEWS_BUTTON, 
                    callback_data="get_notifications_p")],
                [InlineKeyboardButton(
                    text=msg_templates.ARCHIVE_REVIEWS_BUTTON, 
                    callback_data="archive_menu")]
            ])
            
            await message.answer(
                msg_templates.HR_MENU_SELECT,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f'Get new reviews error: {str(e)}')
        await handle_db_error(message)
    
        
# --------------------------
#  Display Handlers
# --------------------------
@hr_commands_router.callback_query(F.data.startswith("notifications_page_"))
async def _handle_notifications_pagination(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        menu_type = parts[2]
        page = int(parts[3])

        if len(parts) > 4:
            archive_type = parts[4]
            full_menu_type = f"{menu_type}_{archive_type}"
        else:
            archive_type = None
            full_menu_type = menu_type
        
        with Session() as db:
            if menu_type == 'n':
                notifications = db.query(HrNotification).filter(
                    HrNotification.status == 'new'
                ).join(Vacancy).all()
            elif menu_type == 'p':
                notifications = db.query(HrNotification).filter(
                    HrNotification.status == 'processing'
                ).join(Vacancy).all()
            elif menu_type == 'a':
                if archive_type == 'approved':
                    notifications = db.query(HrNotification).filter(
                        HrNotification.status == 'approved'
                    ).join(Vacancy).all()
                elif archive_type == 'declined':
                    notifications = db.query(HrNotification).filter(
                        HrNotification.status == 'declined'
                    ).join(Vacancy).all()
                else:
                    notifications = db.query(HrNotification).filter(
                        HrNotification.status.in_(['approved', 'declined'])
                    ).join(Vacancy).all()
            
            await callback.message.edit_reply_markup(
                reply_markup=_build_notifications_keyboard(
                    notifications=notifications, 
                    source_menu=full_menu_type,
                    page=page
                )
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Handle notifications pagination error: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data.startswith("get_notifications_"))
async def _get_notifications_by_status(callback: CallbackQuery):
    '''Фильтрация необходимых решений, в зависимости от выбранного меню'''
    try:
        with Session() as db:
            parts = callback.data.split("_")
            menu_type = parts[2]
            
            if len(parts) > 3:
                archive_type = parts[3]
            else:
                archive_type = None
                
            match menu_type:
                case 'n':
                    text = msg_templates.NEW_REVIEWS
                    notifications = db.query(HrNotification).filter_by(
                        status='new'
                        ).join(Vacancy).all()
                case 'p':
                    text = msg_templates.PROCESSING_REVIEWS
                    notifications = db.query(HrNotification).filter_by(
                        status='processing'
                        ).join(Vacancy).all()
                case 'a':
                    if archive_type == 'approved':
                        text = msg_templates.ARCHIVE_APPROVED
                        notifications = db.query(HrNotification).filter_by(
                            status='approved'
                        ).join(Vacancy).all()
                    elif archive_type == 'declined':
                        text = msg_templates.ARCHIVE_DECLINED
                        notifications = db.query(HrNotification).filter_by(
                            status='declined'
                        ).join(Vacancy).all()
                    else:
                        text = msg_templates.ARCHIVE_REVIEWS
                        notifications = db.query(HrNotification).filter(
                            HrNotification.status.in_(['approved', 'declined'])
                        ).join(Vacancy).all()
                case _:
                    await callback.answer("Недопустипый тип меню")
                    return
            await callback.message.answer(
                text,
                reply_markup=_build_notifications_keyboard(
                    notifications,
                    source_menu=f"{menu_type}_{archive_type}" if archive_type else menu_type
                )
            )
        await callback.answer()    
    except Exception as e:
        logger.error(f'_get_notification_by_status error: {str(e)}')
        await handle_db_error(callback.message) 
    

@hr_commands_router.callback_query(F.data.startswith("notification_detail_"))
async def _show_notification_detail(callback: CallbackQuery, source_menu: str = None):
    '''Показать меню справочной информации по кандидату'''
    try:
        if callback.data.startswith("notification_detail_"):
            parts = callback.data.split("_")
            notification_id = int(parts[2])
            source_menu = parts[3]
            
            if len(parts) > 4 and parts[3] == 'a':
                source_menu = f"{parts[3]}_{parts[4]}"
        else:
            notification_id = int(callback.data.split("_")[-1])
            source_menu = source_menu or 'p'

        with Session() as db:
            notification = db.query(HrNotification).join(
                Candidate
            ).join(
                Vacancy
            ).filter(
                HrNotification.id == notification_id
            ).first()
            
            if not notification:
                await callback.answer("Notification not found")
                return
                
            candidate_name = db.query(Candidate).get(notification.candidate_id).full_name
            vacancy_title = db.query(Vacancy).get(notification.vacancy_id).title
            
            hr_name = None
            if notification.status in ['processing', 'approved', 'declined']:
                hr = notification.application.hr_specialist
                hr_name = hr.full_name

            resume_score: int = None
            resume = notification.application.resume
            resume_score = resume.gigachat_score
            
            detail_text = msg_templates.detail_text_message(
                candidate_name=candidate_name,
                vacancy_title=vacancy_title,
                resume_score=resume_score if resume_score else 'оценка ещё не проводилась',
                telegram_score=notification.analysis_score,
                decision=get_status_display(notification.final_decision)[2:],
                date=notification.sent_at.strftime('%Y-%m-%d'),
                status=get_status_display(notification.status)[2:],
                hr=hr_name
            )
            
            action_buttons = []
            action_buttons.append(InlineKeyboardButton(
                text=msg_templates.GET_CANDIDATE_ANSWERS,
                callback_data=f"get_answers_{notification.id}"
            ))
            action_buttons.append(InlineKeyboardButton(
                text=msg_templates.GET_CANDIDATE_RESUME,
                callback_data=f"get_resume_{notification.id}"
            ))
            
            if notification.status == "new":
                action_buttons.append(InlineKeyboardButton(
                    text=msg_templates.TAKE_TO_PROCESSING,
                    callback_data=f"start_processing_{notification.id}"
                ))
            elif notification.status == "processing":
                action_buttons.append(InlineKeyboardButton(
                    text=msg_templates.REVIEW_APPROVED,
                    callback_data=f"approve_{notification.id}"
                ))
                action_buttons.append(InlineKeyboardButton(
                    text=msg_templates.REVIEW_DECLINED,
                    callback_data=f"decline_{notification.id}"
                ))
            
            keyboard = [
                action_buttons[i:i+2] for i in range(0, len(action_buttons), 2)
            ]
            keyboard.append([InlineKeyboardButton(
                text=msg_templates.BACK_TO_LIST,
                callback_data=f"back_to_list_{source_menu}"
            )])
            await callback.message.edit_text(
                detail_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="MarkdownV2"
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error in show notifications detail: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data == "archive_menu")
async def _show_archive_menu(callback: CallbackQuery):
    try:
        keyboard = _get_archive_keyboard()
        
        await callback.message.edit_text(
            msg_templates.ARCHIVE_TYPE_CHOOSE,
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error showing archive menu: {str(e)}')
        await handle_db_error(callback.message) 



@hr_commands_router.callback_query(F.data.startswith("get_answers_"))
async def _get_candidate_answers(callback: CallbackQuery):
    '''Получить ответы кандидата по его опроснику'''
    try:
        notification_id = int(callback.data.split("_")[-1])
    
        with Session() as db:
            notification = db.query(HrNotification).get(notification_id)
            answers_json = build_json(
                application_id=notification.application_id,
                vacancy_id=notification.vacancy_id
            )
            
            formatted_answers = candidate_answers_formatter(
                answers_json
            )
            
            await callback.message.answer(
                msg_templates.candidate_answers_message(answers=formatted_answers)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error in get answers for candidate: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data.startswith("get_resume_"))
async def _get_candidate_resume(callback: CallbackQuery):
    '''Получить информацию о резюме кандидата'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            notification = db.query(HrNotification).get(notification_id)
            resume = db.query(Resume).filter(
                Resume.candidate_id == notification.candidate_id,
                Resume.application_id == notification.application_id
            ).first()
            
            if resume:
                await callback.message.answer(
                    msg_templates.link_to_candidate_resume_message(link=resume.resume_link),
                    parse_mode="MarkdownV2"
                )
            else:
                await callback.message.answer(msg_templates.NO_RESUME_FOR_REVIEW)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in getting candidate's resume: {str(e)}")
        await handle_db_error(callback.message)


# --------------------------
#  Review Action Handlers
# --------------------------
@hr_commands_router.callback_query(F.data.startswith("start_processing_"))
async def _start_processing(callback: CallbackQuery):
    '''Взять кандидата в обработку'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            hr_to_process = db.query(HrSpecialist).filter_by(
                telegram_id=str(callback.from_user.id)
            ).first()
            
            notification = db.query(HrNotification).get(notification_id)
            notification.status = "processing"
            
            application = notification.application
            application.hr_specialist_id = hr_to_process.id
            
            db.commit()
            
            await callback.answer(msg_templates.MARK_REVIEW_AS_PROCESSING)
            await _show_notification_detail(callback, source_menu='n')
    except Exception as e:
        logger.error(f'Error after start processing review: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data.startswith("approve_"))
async def _approve_candidate(callback: CallbackQuery):
    '''Одорить кандидата, с автоматическим уведомлением в Telegram'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            hr_to_approve = db.query(HrSpecialist).filter_by(
                telegram_id=str(callback.from_user.id)
            ).first()
            
            notification = db.query(HrNotification).get(notification_id)
            notification.status = "approved"
            
            if hr_to_approve.id != notification.application.hr_specialist_id:
                notification.application.hr_specialist_id = hr_to_approve.id
            
            candidate = db.query(Candidate).get(notification.candidate_id)
            candidate.status = "approved"
            candidate.update_at = datetime.utcnow()
            candidate_telegram_id = candidate.telegram_id
            
            application = db.query(Application).get(notification.application_id)
            application.status = "ACCEPTED"
            
            db.commit()
            
            await _notify_candidate(
                bot=callback.bot,
                telegram_id=candidate_telegram_id,
                decision=ACCEPT_DECISION
            )         
            await callback.answer(msg_templates.MARK_REVIEW_AS_ACCEPTED)
            await _show_notification_detail(callback, source_menu='p')
    except Exception as e:
        logger.error(f'Error after approve review: {str(e)}')
        await (callback.message)


@hr_commands_router.callback_query(F.data.startswith("decline_"))
async def _decline_candidate(callback: CallbackQuery):
    '''Отказать кандидату, с автоматическим уведомлением в Telegram'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            hr_to_decline = db.query(HrSpecialist).filter_by(
                telegram_id=str(callback.from_user.id)
            ).first()
            
            notification = db.query(HrNotification).get(notification_id)
            notification.status = "declined"
            
            if hr_to_decline.id != notification.application.hr_specialist_id:
                notification.application.hr_specialist_id = hr_to_decline.id
            
            candidate = db.query(Candidate).get(notification.candidate_id)
            candidate.status = "declined"
            candidate.update_at = datetime.utcnow()
            candidate_telegram_id = candidate.telegram_id
            
            application = db.query(Application).get(notification.application_id)
            application.status = "REJECTED"
            
            db.commit()
            
            await _notify_candidate(
                bot=callback.bot,
                telegram_id=candidate_telegram_id,
                decision=DECLINE_DECISION
            )
            await callback.answer(msg_templates.MARK_REVIEW_AS_DECLINED)
            await _show_notification_detail(callback, source_menu='p')
    except Exception as e:
        logger.error(f'Error after decline review: {str(e)}')
        await handle_db_error(callback.message)


async def _notify_candidate(
    bot: Bot,
    telegram_id: int, 
    decision: bool
):
    '''Уведомить кандидата о результах проверки HR-специалистом'''
    try:
        if decision:
            await bot.send_message(
                chat_id=telegram_id,
                text=msg_templates.TO_ACCEPTED_CANDIDATE
            )
        else:
            await bot.send_message(
                chat_id=telegram_id,
                text=msg_templates.TO_DECLINED_CANDIDATE
            )
    except Exception as e:
        logger.error(f'Error while notifying candidate: {str(e)}')
            

# --------------------------
#  Other Handlers
# --------------------------
@hr_commands_router.callback_query(F.data == "back_to_main_menu")
async def _back_to_main_menu(callback: CallbackQuery):
    try:
        await _get_reviews_selection(callback.message, user=callback.from_user)
        await callback.answer()
    except Exception as e:
        logger.error(f'Error returning to main menu: {str(e)}')
        await handle_db_error(callback.message)
        

@hr_commands_router.callback_query(F.data.startswith("back_to_list_"))
async def _back_to_list(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        menu_type = parts[3]

        if len(parts) > 4:
            archive_type = parts[4]
            full_menu_type = f"{menu_type}_{archive_type}"
        else:
            archive_type = None
            full_menu_type = menu_type
        
        with Session() as db:
            match menu_type:
                case 'n':
                    notifications = db.query(HrNotification).filter_by(
                        status='new'
                    ).join(Vacancy).all()
                    text = msg_templates.NEW_REVIEWS
                case 'p':
                    notifications = db.query(HrNotification).filter_by(
                        status='processing'
                    ).join(Vacancy).all()
                    text = msg_templates.PROCESSING_REVIEWS
                case 'a':
                    if archive_type == 'approved':
                        text = msg_templates.ARCHIVE_APPROVED
                        notifications = db.query(HrNotification).filter(
                            HrNotification.status == 'approved'
                        ).join(Vacancy).all()
                    elif archive_type == 'declined':
                        text = msg_templates.ARCHIVE_DECLINED
                        notifications = db.query(HrNotification).filter(
                            HrNotification.status == 'declined'
                        ).join(Vacancy).all()
                    else:
                        text = msg_templates.ARCHIVE_REVIEWS
                        notifications = db.query(HrNotification).filter(
                            HrNotification.status.in_(['approved', 'declined'])
                        ).join(Vacancy).all()
                case _:
                    await callback.answer("Invalid menu type")
                    return
            
            await callback.message.edit_text(
                text,
                reply_markup=_build_notifications_keyboard(
                    notifications, 
                    source_menu=full_menu_type
                )
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in _back_to_list: {str(e)}")
        await callback.answer("Failed to go back. Please try again.")


@hr_commands_router.callback_query(F.data == "noop")
async def _handle_noop(callback: CallbackQuery):
    '''
        Пустая операция
        Используется для CallbackQuery которые не требуют обработки
        Например: кнопка с текущей страницей в меню пагинации
    '''
    await callback.answer()