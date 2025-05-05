import src.bot.utils.message_templates as msg_templates

from aiogram import F
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.session import Session
from src.database.models import RegistrationToken, HrSpecialist
from src.bot.config import ADMIN_CHANNEL_ID, ADMIN_USER_ID


admin_router = Router()


class DeleteHRStates(StatesGroup):
    waiting_for_confirmation = State()


@admin_router.message(
    Command('generate_token'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def generate_token(message: Message):
    await message.answer(
        msg_templates.COMMAND_ACCEPTED
    )
    
    with Session() as db:
        admin = db.query(HrSpecialist).filter_by(
            telegram_id=str(ADMIN_USER_ID)
        ).first()
        
        admin_name = message.from_user.full_name
        if not admin:
            admin = HrSpecialist(
                telegram_id=str(ADMIN_USER_ID),
                full_name=admin_name if admin_name else 'Администратор',
                is_approved=True
            )
            db.add(admin)
            db.commit()
    
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


@admin_router.message(
    Command('list_hr'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def get_hr_list(message: Message):
    if message.chat.id != ADMIN_CHANNEL_ID:
        await message.answer(
            msg_templates.ACCESS_RESTRICTED,
        )
        return
    
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
        

@admin_router.message(
    Command('delete_hr'),
    F.chat.id == ADMIN_CHANNEL_ID
)
async def delete_hr(
    message: Message,
    state: FSMContext
):
    if message.chat.id != ADMIN_CHANNEL_ID:
        await message.answer(
            msg_templates.ACCESS_RESTRICTED,
        )
        return
    
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


@admin_router.message(
    StateFilter(DeleteHRStates.waiting_for_confirmation),
    F.text.casefold().in_({"да", "yes", "д", "y"})
)
async def confirm_delete(message: Message, state: FSMContext):
    data = await state.get_data()

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


@admin_router.message(
    StateFilter(DeleteHRStates.waiting_for_confirmation)
)
async def cancel_delete(message: Message, state: FSMContext):
    await message.answer(msg_templates.HR_DELETE_CANCELLED)
    await state.clear()
