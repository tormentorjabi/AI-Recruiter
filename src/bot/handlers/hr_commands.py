import logging
import src.bot.utils.message_templates as msg_templates

from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardButton, InlineKeyboardMarkup
)

from sqlalchemy import select, desc, asc
from sqlalchemy.orm import joinedload

from src.database.session import Session
from src.database.models import (
    HrSpecialist, HrNotification, Candidate, Application,
    Vacancy, AnalysisResult, Resume, BotInteraction
)
from src.database.models.hr_notification import NotificationStatus

from src.bot.utils.bot_answers_json_builder import build_json


logger = logging.getLogger(__name__)
hr_commands_router = Router()

class ToggleWorkModeStates(StatesGroup):
    waiting_for_confirmation = State()


def get_status_display(status: str) -> str:
    """Convert status code to human-readable text"""
    status_map = {
        "new": "🆕 Доступен для обработки",
        "processing": "⏳ В обработке",
        "approved": "✅ Одобрен",
        "declined": "❌ Отклонен"
    }
    return status_map.get(status, f"Неизвестный ({status})")

# --------------------------
#  Display Helpers
# --------------------------
def _build_notifications_keyboard(notifications, page=0, items_per_page=5):
    sorted_notifications = sorted(
        notifications,
        key= lambda x: (
            0 if x.status in ["approved", "processing"] else 1,
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
                f"{vacancy_title}\n"
                f"Оценка: {notification.analysis_score:.2f}\n"
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
            

@hr_commands_router.message(Command('change_work_mode'))
async def toggle_work_mode(
    message: Message,
    state: FSMContext
):
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
        

@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation),
    F.text.casefold().in_({"да", "yes", "д", "y"})
)
async def confirm_change_work_mode(message: Message, state: FSMContext):
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
    

@hr_commands_router.message(
    StateFilter(ToggleWorkModeStates.waiting_for_confirmation)
)
async def cancel_change_work_mode(message: Message, state: FSMContext):
    await message.answer(msg_templates.WORK_MODE_CHANGE_CANCELLED)
    await state.clear()

'''
Чел отправляет анкету -> Ответы проходят обработку в нейронке -> Резы сохраняются в БД -> Создаем уведомление для HRов ->>

(оценка ниже проходной) -> Написать кандидату об отказе?

(оценка удовлетворительная для дальнейшей работы с кандидатом) -> Написать кандидату о прохождении порога?

# Доступ только для HR
    /get_reviews -> [Список уведомлений] (Вакансия + Оценка) - Большая клава со списком проверенных кандидатов
    При выборе уведомления ->
        [Уведомление] (Кандидат, Вакансия, Оценка гигачата, [Статус, HR - взявший в работу]) ->
            кнопки: [посмотреть ответы], [посмотреть резюме], [взять в работу]
                    ↑ <все  ответы>      ↑                           ↑ 
                                         ↑ <достать инфу о резюме>   ↑
                                                                     ↑ <сменить статус на "В работе">              
'''

@hr_commands_router.message(Command("get_reviews"))
async def get_reviews(message: Message):
    with Session() as db:
        hr = db.query(HrSpecialist).filter_by(
            telegram_id=str(message.from_user.id),
            is_approved=True
        ).first()

        if not hr:
            await message.answer(msg_templates.NOT_REGISTERED_AS_HR)
            return
            
        notifications = db.query(HrNotification).join(
            Vacancy
        ).filter(
            HrNotification.hr_specialist_id == hr.id
        ).all()
        
        if not notifications:
            await message.answer(msg_templates.EMPTY_REVIEWS)
            return
            
        await message.answer(
            msg_templates.AVAILABLE_REVIEWS,
            reply_markup=_build_notifications_keyboard(notifications)
        )


# Pagination handler
@hr_commands_router.callback_query(F.data.startswith("notifications_page_"))
async def handle_notifications_pagination(callback: CallbackQuery):
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


# Notification detail view
@hr_commands_router.callback_query(F.data.startswith("notification_detail_"))
async def show_notification_detail(callback: CallbackQuery):
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
            date=notification.sent_at.strftime('%Y-%m-%d %H:%M'),
            status=get_status_display(notification.status)
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
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


# Action handlers
@hr_commands_router.callback_query(F.data.startswith("get_answers_"))
async def get_candidate_answers(callback: CallbackQuery):
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


@hr_commands_router.callback_query(F.data.startswith("get_resume_"))
async def get_candidate_resume(callback: CallbackQuery):
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


@hr_commands_router.callback_query(F.data.startswith("start_processing_"))
async def start_processing(callback: CallbackQuery):
    notification_id = int(callback.data.split("_")[-1])
    
    with Session() as db:
        notification = db.query(HrNotification).get(notification_id)
        notification.status = "processing"
        db.commit()
        
        await callback.answer(msg_templates.MARK_REVIEW_AS_PROCESSING)
        await show_notification_detail(callback)


@hr_commands_router.callback_query(F.data.startswith("approve_"))
async def approve_candidate(callback: CallbackQuery):
    notification_id = int(callback.data.split("_")[-1])
    
    with Session() as db:
        notification = db.query(HrNotification).get(notification_id)
        notification.status = "approved"
        
        application = db.query(Application).get(notification.application_id)
        application.status = "accepted"
        
        db.commit()
        
        # TODO:
        # Уведомить кандидата
        await callback.answer(msg_templates.MARK_REVIEW_AS_ACCEPTED)
        await show_notification_detail(callback)


@hr_commands_router.callback_query(F.data.startswith("decline_"))
async def decline_candidate(callback: CallbackQuery):
    notification_id = int(callback.data.split("_")[-1])
    
    with Session() as db:
        notification = db.query(HrNotification).get(notification_id)
        notification.status = "declined"
        
        application = db.query(Application).get(notification.application_id)
        application.status = "rejected"
        
        db.commit()
        
        # TODO:
        # Уведомить кандидата
        await callback.answer(msg_templates.MARK_REVIEW_AS_DECLINED)
        await show_notification_detail(callback)


@hr_commands_router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    await get_reviews(callback.message)
    await callback.answer()