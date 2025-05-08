import logging

import src.bot.utils.message_templates as msg_templates

from typing import List
from sqlalchemy import desc
from aiogram import F
from aiogram import Router
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.session import Session
from src.database.models import (
    RegistrationToken, HrSpecialist, Vacancy,
    Application, BotQuestion
)
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID
from src.bot.utils.error_handlers import handle_db_error


logger = logging.getLogger(__name__)
admin_router = Router()


class DeleteHRStates(StatesGroup):
    waiting_for_confirmation = State()


#---------------
# Display Utilites
#---------------
def _build_vacancies_keyboard(vacancies: List[Vacancy], page: int = 0, items_per_page: int = 10):
    total_pages = (len(vacancies) + items_per_page - 1) // items_per_page
    page_vacancies = vacancies[page*items_per_page:(page+1)*items_per_page]
    
    keyboard = []
    for vacancy in page_vacancies:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📄 {vacancy.title}",
                callback_data=f"vacancy_detail_{vacancy.id}"
            )
        ])
        
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(
                text="◀️", 
                callback_data=f"vacancies_page_{page-1}"
            ))
        pagination.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", 
            callback_data="noop"
        ))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(
                text="▶️", 
                callback_data=f"vacancies_page_{page+1}"
            ))
        keyboard.append(pagination)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@admin_router.callback_query(F.data.startswith("vacancies_page_"))
async def _handle_vacancies_pagination(callback: CallbackQuery):
    try:
        page = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).all()
            
            await callback.message.edit_reply_markup(
                reply_markup=_build_vacancies_keyboard(vacancies, page=page)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error in vacancies pagination: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Init Handlers
#---------------
@admin_router.message(
    Command('start'),
    F.chat.id == ADMIN_CHANNEL_ID,
    F.from_user.id == ADMIN_USER_ID
)
async def _start_as_admin(message: Message):
    try:
        with Session() as db:
            admin = db.query(HrSpecialist).filter_by(
                telegram_id=str(ADMIN_USER_ID)
            ).first()
            user_full_name = message.from_user.full_name
            admin_name = user_full_name if user_full_name else 'Администратор'
            
            if not admin:
                admin = HrSpecialist(
                telegram_id=str(ADMIN_USER_ID),
                full_name=admin_name,
                is_approved=True)
                db.add(admin)
                db.commit()
                
                await message.answer(
                    msg_templates.show_admin_helper_message(admin_name=admin_name),
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    msg_templates.show_admin_helper_message(admin_name=admin_name),
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f'Error in start_as_admin: {str(e)}')
        await handle_db_error(message)
    

#---------------
# Main Commands Handlers
#---------------
@admin_router.message(
    Command('list_vacancies'),
    F.chat.id == ADMIN_CHANNEL_ID,
    F.from_user.id == ADMIN_USER_ID
)
async def _list_vacancies(message: Message):
    try:
        with Session() as db:
            vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).all()
            
            if not vacancies:
                await message.answer('В системе нет вакансий')
                return
            
            await message.answer(
                "Список вакансий:",
                reply_markup=_build_vacancies_keyboard(vacancies)
            )
    except Exception as e:
        logger.error(f'Error while trying to list vacancies: {str(e)}')
        handle_db_error(message)


@admin_router.message(
    Command('generate_token'),
    F.chat.id == ADMIN_CHANNEL_ID,
    F.from_user.id == ADMIN_USER_ID
)
async def _generate_token(message: Message):
    await message.answer(
        msg_templates.COMMAND_ACCEPTED
    )
    try:
        with Session() as db:
            admin = db.query(HrSpecialist).filter_by(
                telegram_id=str(ADMIN_USER_ID)
            ).first()
            
            # Токены живут 24 часа (настраиваемо)
            token = RegistrationToken.generate_token(admin.id)
            generated_token = token.token
            
            db.add(token)
            db.commit()
        
        await message.answer(
            msg_templates.registration_token_message(
                generated_token=generated_token
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f'Error while trying to generate token: {str(e)}')
        await handle_db_error(message)


@admin_router.message(
    Command('list_hr'),
    F.chat.id == ADMIN_CHANNEL_ID,
    F.from_user.id == ADMIN_USER_ID
)
async def _get_hr_list(message: Message):
    try:
        with Session() as db:
            hrs = db.query(HrSpecialist).filter_by(
                    is_approved=True
                ).order_by(HrSpecialist.created_at.desc()).all()
            
            if not hrs:
                await message.answer(
                    msg_templates.NO_HRS_TO_LIST
                )
                return
                
            response = "Список зарегистрированных HR-специалистов:\n\n"
            for hr in hrs:
                response += (
                    msg_templates.list_hr_instance_info_message(
                        hr_full_name=hr.full_name,
                        hr_telegram_id=hr.telegram_id,
                        hr_created_at=hr.created_at.strftime('%d.%m.%Y %H:%M')
                    )
                )
            
            await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f'Error while tryin to list HRs: {str(e)}')
        handle_db_error(message)
        

@admin_router.message(
    Command('delete_hr'),
    F.chat.id == ADMIN_CHANNEL_ID,
    F.from_user.id == ADMIN_USER_ID
)
async def _delete_hr(
    message: Message,
    state: FSMContext
):
    try:
        args = message.text.split(maxsplit=1)[1:] if len(message.text.split()) > 1 else []
        
        if not args:
            await message.answer(
                msg_templates.SHOW_DELETE_HR_COMMAND_HELPER,
                parse_mode="Markdown"
            )
            return

        telegram_id = args[0].strip()

        if telegram_id == str(ADMIN_USER_ID):
            await message.answer(
            msg_templates.SYSTEM_ADMIN_DELETE_PREVENTED
            )
            return
        
        with Session() as db:
            hr = db.query(HrSpecialist).filter_by(
                    is_approved=True,
                    telegram_id=telegram_id
                ).first()
            
            if not hr:
                await message.answer(
                    msg_templates.hr_with_id_not_found_message(telegram_id=telegram_id),
                    parse_mode="Markdown"
                )
                await message.answer(
                    msg_templates.SHOW_LIST_HR_COMMAND_HELPER,
                    parse_mode="Markdown"
                )
                return
            
            await state.update_data(hr_id=hr.id, telegram_id=telegram_id)
            await message.answer(
                msg_templates.confirm_delete_hr_message(
                    hr_full_name=hr.full_name,
                    telegram_id=telegram_id
                )
            )
            await state.set_state(DeleteHRStates.waiting_for_confirmation)
    except Exception as e:
        logger.error(f'Error while trying to delete HR: {str(e)}')
        handle_db_error(message)


#---------------
# Callback Handlers
#---------------
@admin_router.callback_query(F.data.startswith("vacancy_detail_"))
async def _show_vacancy_detail(callback: CallbackQuery):
    try:
        vacancy_id = int(callback.data.split("_")[-1])
        
        with Session() as db:
            vacancy = db.query(Vacancy).get(vacancy_id)
            if not vacancy:
                await callback.answer("Вакансия не найдена")
                return
            
            application_count = db.query(Application).filter_by(
                vacancy_id=vacancy_id
            ).count()
            
            detail_text = (
                f"📌 Вакансия: {vacancy.title}\n\n"
                f"🆔 ID: {vacancy.id}\n"
                f"📝 Описание: {vacancy.description}\n"
                f"📅 Создана: {vacancy.created_at.strftime('%Y-%m-%d')}\n"
                f"📅 Откликов: {application_count}\n"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔙 Просмотреть параметры вакансии",
                    callback_data=f"vacancy_params_{vacancy_id}"
                )],
                
                [InlineKeyboardButton(
                    text="🔙 Редактировать параметры вакансии",
                    callback_data=f"edit_vacancy_params_{vacancy_id}"
                )],

                [InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data="back_to_vacancies_list"
                )]
            ])
            
            await callback.message.edit_text(
                detail_text,
                reply_markup=keyboard
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error showing vacancy detail: {str(e)}')
        await handle_db_error(callback.message)


@admin_router.callback_query(F.data == "back_to_vacancies_list")
async def _back_to_vacancies_list(callback: CallbackQuery):
    """Return to vacancies list from detail view"""
    try:
        with Session() as db:
            vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).all()
            
            await callback.message.edit_text(
                "📋 Список вакансий в системе:",
                reply_markup=_build_vacancies_keyboard(vacancies)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f'Error returning to vacancies list: {str(e)}')
        await handle_db_error(callback.message)


#---------------
# Confirmation Handlers
#---------------
@admin_router.message(
    StateFilter(DeleteHRStates.waiting_for_confirmation),
    F.text.casefold().in_({"да", "yes", "д", "y"})
)
async def _confirm_delete_hr(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        with Session() as db:
            hr = db.query(HrSpecialist).get(data['hr_id'])

            if not hr:
                await message.answer(msg_templates.HR_NOT_FOUND_IN_DATABASE)
                await state.clear()
                return

            db.query(RegistrationToken).filter_by(used_by=hr.id).delete()
            db.delete(hr)
            db.commit()

            await message.answer(
                msg_templates.hr_deleted_message(
                    hr_full_name=hr.full_name,
                    telegram_id=data['telegram_id']
                ),
                parse_mode="Markdown"
            )

        await state.clear()
    except Exception as e:
        logger.error(f'Error in confirm HR delete: {str(e)}')
        handle_db_error(message)


@admin_router.message(
    StateFilter(DeleteHRStates.waiting_for_confirmation)
)
async def _cancel_delete_hr(message: Message, state: FSMContext):
    await message.answer(msg_templates.HR_DELETE_CANCELLED)
    await state.clear()


@admin_router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    '''
        Пустая операция
        Используется для CallbackQuery которые не требуют обработки
        Например: кнопка с текущей страницей в меню пагинации
    '''
    await callback.answer()