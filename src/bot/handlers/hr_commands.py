import logging
import src.bot.utils.message_templates as msg_templates

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardButton, InlineKeyboardMarkup
)
from datetime import datetime

from src.database.session import Session
from src.database.models import (
    HrSpecialist, HrNotification, Candidate, 
    Application, Vacancy, Resume
)

from src.bot.utils.bot_answers_json_builder import build_json
from src.bot.utils.handle_error import handle_db_error


logger = logging.getLogger(__name__)
hr_commands_router = Router()

class ToggleWorkModeStates(StatesGroup):
    waiting_for_confirmation = State()


# --------------------------
#  Confirmation Handlers
# --------------------------
@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation),
    F.text.casefold().in_({"да", "yes", "д", "y"})
)
async def _confirm_change_work_mode(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        
        with Session() as db:
            hr = db.query(HrSpecialist).get(data['hr_id'])
        
            if not hr:
                await message.answer(msg_templates.HR_NOT_FOUND_IN_DATABASE)
                await state.clear()
                return

            new_status = not hr.work_mode
            hr.work_mode = new_status
            db.commit()

            status_text = "Активен" if new_status else "Не активен"
            await message.answer(
            msg_templates.work_mode_changed_message(
                status_text=status_text,
                status=new_status
            ),
            parse_mode="Markdown"
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error in confirm change work mode: {str(e)}")
        await handle_db_error(message)
    

@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation)
)
async def _cancel_change_work_mode(message: Message, state: FSMContext):
    await message.answer(msg_templates.WORK_MODE_CHANGE_CANCELLED)
    await state.clear()


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


def _build_notifications_keyboard(notifications, page=0, items_per_page=5):
    # Сортируем все решения по следующему принципу:
    # 1. В обработке (отсортированы по уменьшению оценки GigaChat)
    # 2. Новые (отсортированы по уменьшению оценки GigaChat)
    # 3. Одобренные (отсортированы по уменьшению оценки GigaChat)
    # 4. Отказанные (отсортированы по уменьшению оценки GigaChat)
    sorted_notifications = sorted(
        notifications,
        key=lambda x: (
            {"processing": 0, "new": 1, "approved": 2, "declined": 3}.get(x.status, 4),
            -x.analysis_score if x.analysis_score else 0
        )
    )
    
    total_pages = (len(sorted_notifications) + items_per_page - 1) // items_per_page
    page_notifications = sorted_notifications[page*items_per_page:(page+1)*items_per_page]
    
    keyboard = []
    with Session() as db:
        for notification in page_notifications:
            vacancy = db.query(Vacancy).get(notification.vacancy_id)
            vacancy_title = vacancy.title
            btn_text = (
                f"{vacancy_title[:15]} | "
                f"Оценка: {notification.analysis_score:.2f} | "
                f"{get_status_display(notification.status)}"
            )
            keyboard.append([
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"notification_detail_{notification.id}"
                )
            ])
    
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(
                text="◀️", 
                callback_data=f"notifications_page_{page-1}"
            ))
        pagination.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", 
            callback_data="noop"
        ))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(
                text="▶️", 
                callback_data=f"notifications_page_{page+1}"
            ))
        keyboard.append(pagination)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

   
# --------------------------
#  Init Commands Handlers
# --------------------------
@hr_commands_router.message(Command('change_work_mode'))
async def _toggle_work_mode(
    message: Message,
    state: FSMContext
):
    try:
        with Session() as db:
            hr = db.query(HrSpecialist).filter_by(
                telegram_id=str(message.from_user.id),
                is_approved=True
            ).first()

            if not hr:
                await message.answer(msg_templates.NOT_REGISTERED_AS_HR)
                return
            
            hr_work_mode = hr.work_mode
            
            await state.update_data(hr_id=hr.id)
            await message.answer(
                    msg_templates.confirm_change_work_mode_message(work_mode=hr_work_mode),
                )
            await state.set_state(ToggleWorkModeStates.waiting_for_confirmation)
    except Exception as e:
        logger.error(f"Error in change work mode: {str(e)}")
        await handle_db_error(message)


@hr_commands_router.message(Command("get_reviews"))
async def _get_reviews(message: Message, user=None):
    '''Получить список решений, готовых к обработке специалистами'''
    try:
        with Session() as db:
            user_id = user.id if user else message.from_user.id
            
            hr = db.query(HrSpecialist).filter_by(
                telegram_id=str(user_id),
                is_approved=True
            ).first()

            if not hr:
                await message.answer(msg_templates.NOT_REGISTERED_AS_HR)
                return

            notifications = db.query(HrNotification).join(Vacancy).all()
            
            if not notifications:
                await message.answer(msg_templates.EMPTY_REVIEWS)
                return
                
            await message.answer(
                msg_templates.AVAILABLE_REVIEWS,
                reply_markup=_build_notifications_keyboard(notifications)
            )
    except Exception as e:
        logger.error(f'Get reviews error: {str(e)}')
        await handle_db_error(message)
      
        
# --------------------------
#  Display Handlers
# --------------------------
@hr_commands_router.callback_query(F.data.startswith("notifications_page_"))
async def _handle_notifications_pagination(callback: CallbackQuery):
    try:
        page = int(callback.data.split("_")[-1])
        with Session() as db:
            hr = db.query(HrSpecialist).filter(
                HrSpecialist.telegram_id == str(callback.from_user.id)
            ).first()
            
            notifications = db.query(HrNotification).join(
                Vacancy
            ).filter(
                HrNotification.hr_specialist_id == hr.id
            ).all()
            
            await callback.message.edit_reply_markup(
                reply_markup=_build_notifications_keyboard(notifications, page)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Handle notifications pagination error: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data.startswith("notification_detail_"))
async def _show_notification_detail(callback: CallbackQuery):
    '''Показать меню справочной информации по кандидату'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
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
            
            detail_text = msg_templates.detail_text_message(
                candidate_name=candidate_name,
                vacancy_title=vacancy_title,
                score=notification.analysis_score,
                decision=get_status_display(notification.final_decision)[2:],
                date=notification.sent_at.strftime('%Y-%m-%d %H:%M'),
                status=get_status_display(notification.status)[2:]
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
                callback_data="back_to_list"
            )])
            
            await callback.message.edit_text(
                detail_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error in show notifications detail: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data.startswith("get_answers_"))
async def _get_candidate_answers(callback: CallbackQuery):
    '''Получить ответы кандидата по его опроснику'''
    try:
        notification_id = int(callback.data.split("_")[-1])
    
        with Session() as db:
            notification = db.query(HrNotification).get(notification_id)
            formatted_answers = build_json(
                application_id=notification.application_id,
                vacancy_id=notification.vacancy_id
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
                # TODO:
                # Возвращать ссылку на резюме? Надо хранить его в БД тогда
                await callback.message.answer(f"ID Резюме в БД: {resume.id}")
                # await callback.message.answer_document(resume.file_id)
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
            notification = db.query(HrNotification).get(notification_id)
            notification.status = "processing"
            db.commit()
            
            await callback.answer(msg_templates.MARK_REVIEW_AS_PROCESSING)
            await _show_notification_detail(callback)
    except Exception as e:
        logger.error(f'Error after start processing review: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data.startswith("approve_"))
async def _approve_candidate(callback: CallbackQuery):
    '''Одорить кандидата, с автоматическим уведомлением в Telegram'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            notification = db.query(HrNotification).get(notification_id)
            notification.status = "approved"
            
            candidate = db.query(Candidate).get(notification.candidate_id)
            candidate.status = "approved"
            candidate.update_at = datetime.utcnow()
            
            application = db.query(Application).get(notification.application_id)
            application.status = "ACCEPTED"
            
            db.commit()
            
            # TODO:
            # Уведомить кандидата         
            await callback.answer(msg_templates.MARK_REVIEW_AS_ACCEPTED)
            await _show_notification_detail(callback)
    except Exception as e:
        logger.error(f'Error after approve review: {str(e)}')
        await (callback.message)


@hr_commands_router.callback_query(F.data.startswith("decline_"))
async def _decline_candidate(callback: CallbackQuery):
    '''Отказать кандидату, с автоматическим уведомлением в Telegram'''
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            notification = db.query(HrNotification).get(notification_id)
            notification.status = "declined"
            
            candidate = db.query(Candidate).get(notification.candidate_id)
            candidate.status = "declined"
            candidate.update_at = datetime.utcnow()
            
            application = db.query(Application).get(notification.application_id)
            application.status = "REJECTED"
            
            db.commit()
            
            # TODO:
            # Уведомить кандидата
            await callback.answer(msg_templates.MARK_REVIEW_AS_DECLINED)
            await _show_notification_detail(callback)
    except Exception as e:
        logger.error(f'Error after decline review: {str(e)}')
        await handle_db_error(callback.message)


@hr_commands_router.callback_query(F.data == "back_to_list")
async def _back_to_list(callback: CallbackQuery):
    await _get_reviews(callback.message, user=callback.from_user)
    await callback.answer()
    
    
# --------------------------
#  Handle NO-OP
# --------------------------
@hr_commands_router.callback_query(F.data == "noop")
async def _handle_noop(callback: CallbackQuery):
    '''
        Пустая операция
        Используется для CallbackQuery которые не требуют обработки
        Например: кнопка с текущей страницей в меню пагинации
    '''
    await callback.answer()