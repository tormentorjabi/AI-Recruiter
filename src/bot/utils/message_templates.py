#-----------------
# General constants
#-----------------
ACCESS_RESTRICTED = (
    "🚫 Вызов команды из этого чата недоступен"
)

COMMAND_ACCEPTED = (
    "⚙️ Запрос получен, ожидайте\n"
)


#-----------------
# Constants used in candidate_commands.py
#-----------------
def get_candidate_on_start_bot_interaction_message(
    db_candidate_full_name: str, 
    vacancy_title: str, 
    questions_length: int
) -> str:
    return (
        f"Приветствуем вас, {db_candidate_full_name}!\n\n"
        f"В рамках вашего отклика по вакансии: `{vacancy_title}` "
        f"вам необходимо пройти опрос, состоящий из `{questions_length} вопросов`.\n"
        "Без прохождения данного опроса, мы не сможем вынести окончательное решение "
        "по вашей кандидатуре.\n\n"
        "Перед отправкой анкеты, вы сможете увидеть все ответы, данные вами, "
        "а также при необходимости изменить каждый из них.\n\n"
        "Вы не ограничены по времени\n"
        "Вы в любой момент можете прервать сессию прохождения опроса\n\n"
        "Удачи 👍🏻"
    )

CANDIDATE_CANCELLED_FORM = (
    "❌ Процесс прохождения отменен.\n\n"
    "Ваши ответы будут сохранены ближайшие `24 часа`, "
    "затем ответы придется заполнять заново.\n\n"
    "Для возобновления используйте /start"
)

CANDIDATE_NOT_FOUND = (
    "⚠️ Вы не зарегистрированы как соискатель."
)

CANDIDATE_APPLICATIONS_NOT_FOUND = (
    "❌ Нет активных откликов по вакансиям, "
    "которые нуждались бы в прохождении опроса.\n\n"
    "Если вы недавно заполняли форму, "
    "пожалуйста, дождитесь нашего ответа!"
)

VACANCY_QUESTIONS_NOT_FOUND = (
    "⚠️ Для вакансии нет вопросов"
)

CANDIDATE_BOT_INTERACTION_SESSION_TIMEOUT = (
    "❌ Сессия истекла, начните заново"
)

QUESTION_NOT_FOUND = (
    "❌ Вопрос не найден"
)

FILE_EXPECTED = (
    "❌ Ожидается файл"
)

FORM_ALREADY_SUBMITTED = (
    "⚠️ Вы уже отправили эту анкету"
)

ON_FORM_SUBMIT = (
    "✅ Анкета успешно отправлена! Мы свяжемся с вами по результатам."
)

CANDIDATE_FORM_REMINDER = (
    "📝 **Напоминание о незавершенной анкете!**\n"
    "Вы начали заполнять анкету, но не завершили процесс. "
    "Напоминаем, что ваши ответы сохраняются только `12 часов`, "
    "до момента истечения, вы можете продолжить с того места, где остановились.\n"
    "Для продолжения заполнения, отправьте команду /start"
)


#-----------------
# Constants used in admin_commands.py
#-----------------
def registration_token_message(generated_token: str) -> str:
    return (
        "Токен для регистрации HR-специалиста:\n"
        f"`{generated_token}`\n\n"
        "Время действия токена `24` часа!"
    )

def hr_with_id_not_found_message(telegram_id: str) -> str:
    return (
        f"❌ HR-специалист с ID `{telegram_id}` не найден\n"
    )

def list_hr_instance_info_message(
    hr_full_name: str,
    hr_telegram_id: str,
    hr_created_at: str,
    hr_work_mode: bool
) -> str:
    return (
        f"• {hr_full_name}\n"
        f"  Telegram ID: `{hr_telegram_id}`\n"
        f"  Дата регистрации: {hr_created_at}\n"
        f"  Текущий режим работы: `{"Активен" if hr_work_mode else "Не активен"}`\n\n"
    )

def confirm_delete_hr_message(hr_full_name: str, telegram_id: str) -> str:
    return (
        "⚠️ Вы уверены, что хотите удалить HR-специалиста:\n"
        f"Имя: {hr_full_name}\n"
        f"ID: {telegram_id}\n\n"
        "Введите [Да/Нет] для подтверждения:"
    )

def hr_deleted_message(hr_full_name: str, telegram_id: str) -> str:
    return (
        f"✅ HR-специалист {hr_full_name} (ID: {telegram_id}) удален"
    )


SHOW_DELETE_HR_COMMAND_HELPER = (
    "❌ Использование: /delete_hr <Telegram ID HR-специалиста>\n"
    "Пример: /delete_hr 123456789"
)

SHOW_LIST_HR_COMMAND_HELPER = (
    "Найти ID необходимого сотрудника можно с помощью команды: "
    "/list_hr"
)

SYSTEM_ADMIN_DELETE_PREVENTED = (
    "❌ Предотвращено удаление системного администратора"
)

NO_HRS_TO_LIST = (
    "❌ В системе нет зарегистрированных HR-специалистов\n\n"
    "Для регистрации, воспользуйтесь командами создания токенов "
    "и раздайте их сотрудникам!"
)

HR_NOT_FOUND_IN_DATABASE = (
    "❌ HR-специалист не найден в базе данных"
)

HR_DELETE_CANCELLED = (
    "❌ Удаление отменено пользователем"
)


#-----------------
# Constants used in hr_commands.py
#-----------------
def confirm_change_work_mode_message(work_mode: bool) -> str:
    return (
        "Режим получения уведомлений:\n"
        f"{'✅ Активен' if work_mode else '❌ Не активен'}\n\n"
        "Хотите сменить режим?\n"
        "Введите [Да/Нет] для подтверждения:"
    )

def work_mode_changed_message(
    status_text: str,
    status: bool
) -> str:
    return (
        f"🆕 Режим работы изменен на: `{status_text}`\n" +
        f"Уведомления о кандидатах: {'✅ Включены' if status else '❌ Выключены'}"
    )

NOT_REGISTERED_AS_HR = (
    "⚠️ Вы не зарегистрированы как HR-специалист.\n"
    "Если вы желаете зарегистрироваться как HR, запросите "
    "токен регистрации у вашего администратора и выполните "
    "команду /register_hr"
)

WORK_MODE_CHANGE_CANCELLED = (
    "❌ Изменение режима работы отменено пользователем"
)


#-----------------
# Constants used in hr_registration.py
#-----------------
def hr_registered_message(hr_full_name: str) -> str:
    return (
        "✅ Регистрация успешно завершена!\n\n"
        f"Добро пожаловать, {hr_full_name}!\n"
        "Чтобы начать получать уведомления о новых кандидатах "
        "воспользуйтесь командой /change_work_mode"
    )

def hr_registered_notification_message(
    hr_full_name: str,
    telegram_id: str    
) -> str:
    return (
        f"🆕 Новый HR зарегистрирован: "
        f"[{hr_full_name}](tg://user?id={telegram_id})\n"
        f"ID: `{telegram_id}`"
    )


HR_ALREADY_EXISTS = (
    "⚠️ Вы уже зарегистрированы как HR-специалист!\n"
    "Если у вас возникли вопросы по работе бота, "
    "обратитесь к администратору системы."
)

INPUT_REGISTRATION_TOKEN = (
    "Введите регистрационный токен, выданный администратором:"
)

HR_ALREADY_EXISTS_WHILE_IN_REGISTRATION_PROCESS = (
    "⚠️ Обнаружена существующая регистрация!\n"
    "Если это ошибка, обратитесь к администратору."
)

BAD_REGISTRATION_TOKEN = (
    "❌ Неверный или несуществующий токен"
)

TOKEN_ALREADY_IN_USE = (
    "❌ Данный токен уже был задействован. "
    "Запросите новый токен у администратора системы"
)

TOKEN_EXPIRED = (
    "❌ Срок действия токена истек. "
    "Запросите новый токен у администратора системы и повторите регистрацию"
)