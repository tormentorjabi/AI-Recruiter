from typing import Optional, Union
from aiogram.utils.markdown import bold

def escape_markdown(text: str) -> str:
    """Экранирование запрещенных в MarkdownV2 символов"""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

#-----------------
# General constants
#-----------------
ACCESS_RESTRICTED = (
    "🚫 Вызов команды из этого чата недоступен"
)

COMMAND_ACCEPTED = (
    "⚙️ Запрос получен, ожидайте\n"
)

EMPTY_BUTTON = "____________________________________________________"

BACK_TO_LIST = (
    "🔙 Назад к списку"
)

#-----------------
# Constants used in candidate_commands.py
#-----------------
def get_candidate_on_start_bot_interaction_message(
    db_candidate_full_name: Optional[str], 
    vacancy_title: str, 
    questions_length: int
) -> str:
    return (
        f"Приветствуем вас, {db_candidate_full_name if db_candidate_full_name else "уважаемый кандидат"}!\n\n"
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
    "Для возобновления используйте */start*"
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

CANDIDATE_BOT_INTERACTION_NOT_FOUND = (
    "❌ У вас нет активной сессии прохождения анкеты.\n\n"
    "Пожалуйста, воспользуйтесь командой */start*"
)

CANDIDATE_CONSENT_DECLINED_THANKYOU = (
    "Спасибо за ваш ответ.\n\n😔 Мы сожалеем, что вы отказались от обработки персональных данных."
)

CONSENT_AGREE_BUTTON = "✅ Да, согласен"
CONSENT_DECLINE_BUTTON = "❌ Нет, не согласен"

CANDIDATE_CONSENT_REQUEST = (
    "Перед началом работы нам необходимо ваше согласие на обработку персональных данных.\n\n"
    "🔐 Мы обрабатываем ваши данные исключительно в целях рассмотрения вашей кандидатуры на вакансию и не передаём их третьим лицам.\n\n"
    "*Пожалуйста, подтвердите ваше согласие на обработку персональных данных:*"
)

CANDIDATE_CONSENT_DECLINED = (
    "❌ *Вы отказались от обработки персональных данных.*\n\n"
    "К сожалению, мы не можем продолжить рассмотрение вашей кандидатуры без вашего согласия.\n\n"
)

CANDIDATE_CONSENT_RETRY = (
    "⚠️ *Без вашего согласия на обработку персональных данных мы не сможем продолжить рассмотрение вашей кандидатуры.*\n\n"
    "*Пожалуйста, подтвердите согласие для продолжения:*"
)

VACANCY_QUESTIONS_NOT_FOUND = (
    "⚠️ Прохождение анкеты для вакансии, на которую вы откикнулись, не настроено!\n"
    "Решение по вашей кандидатуре будет проводиться классическим методом."
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
    "📝 *Напоминание о незавершенной анкете!*\n\n"
    "Вы начали заполнять анкету, но не завершили процесс.\n\n"
    "Напоминаем, что ваши ответы сохраняются только `24 часа`, "
    "до момента истечения, вы можете продолжить с того места, где остановились.\n\n"
    "Для продолжения заполнения, отправьте команду */start*"
)

TOKEN_AUTH_REQUEST = (
    "👋 Приветствуем вас! Для продолжения работы с ботом, пожалуйста, введите токен, который был отправлен вам для доступа к анкете.\n\n"
    "Токен выглядит как комбинация латинских букв, цифр и символов."
)

TOKEN_AUTH_INVALID = (
    "❌ Введенный токен недействителен или срок его действия истек.\n\n"
    "Пожалуйста, проверьте правильность ввода или обратитесь к HR-специалисту для получения нового токена."
)

TOKEN_AUTH_SUCCESS = (
    "✅ *Аутентификация успешна!*\n\n"
    "Ваш Telegram аккаунт успешно привязан к вашему отклику. Теперь вы можете приступить к процессу заполнения анкеты."
)

NO_ACTIVE_SESSION_FOUND_TO_CANCEL = (
    "У вас нет активной анкеты, которую можно отменить.\n"
    "Если вы *кандидат*, который приглашен к прохождению анкеты, воспользуйтесь командой */start* "
    "и следуйте инструкциям в последующем сообщении.\n\n"
    "Если вы *HR-специалист*, запросите токен регистрации у Администратора вашей системы и "
    "воспользуйтесь командой */register_hr*"
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
    hr_created_at: str
) -> str:
    return (
        f"• {hr_full_name}\n"
        f"  Telegram ID: `{hr_telegram_id}`\n"
        f"  Дата регистрации: {hr_created_at}\n\n"
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

ASK_FOR_ADMIN_REGISTRATION_HELPER = (
    "❌ Пожалуйста, воспользуйтесь */start*, для регистрации в качестве Администратора"
) 

def show_admin_helper_message(admin_name: str) -> str:
    return (
        f"Добрый день, *{admin_name}*!\n\n"
        "🧑‍💻 Команды HR:\n"
        "*/get_reviews* - Меню HR-специалиста\n\n"
        "🤖 Команды Администратора:\n"
        "*/list_vacancies* - Меню настроек параметров вакансий\n"
        "*/generate_token* - Генерация токена регистрации HR\n"
        "*/list_hrs* - Список HR-специалистов в системе\n"
        "*/delete_hr* - Удалить HR-специалиста из системы\n\n"
        "⚠️ Тестовые команды для демо:\n"
        "`/send Оператор контактного центра https://hh.ru/resume/0343600aff0c1b1b130039ed1f4a7a6e7a494c`\n\n"
        "`/send Оператор контактного центра https://nizhny-tagil.hh.ru/resume/27597eb2ff0e7799050039ed1f494d63716948`\n"
    )
    
SHOW_SEND_COMMAND_HELPER = (
    "❌ Использование: */send <вакансия> <url резюме>*\n\n"
    "Пример:\n*/send Оператор https://hh.ru/resume/1234567890abcdefg*\n\n"
    "🗄 Доступные вакансии для тестирования:\n"
    "`/send Оператор контактного центра` *<url вашего резюме>*"
)  
  
    
SHOW_DELETE_HR_COMMAND_HELPER = (
    "❌ Использование: */delete_hr <Telegram ID HR-специалиста>*\n"
    "Пример: */delete_hr 123456789*"
)

SHOW_LIST_HR_COMMAND_HELPER = (
    "Найти ID необходимого сотрудника можно с помощью команды: "
    "*/list_hr*"
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
def link_to_candidate_resume_message(link: str) -> str:
    return (
        f"[{escape_markdown("Ссылка на резюме кандидата на HH.ru")}]({link})"
    )

def detail_text_message(
    candidate_name: str,
    vacancy_title: str,
    resume_score: Union[int, str],
    telegram_score: int,
    decision: str,
    date,
    status: str,
    hr: Optional[str]
) -> str:
    hr_info = ""
    if hr:
        hr_info = f"🧑‍💻 HR курирующий отклик: {bold(escape_markdown(hr))}"
    return (
            f"👤 Кандидат: {escape_markdown(candidate_name)}\n\n"
            f"📌 Вакансия: {escape_markdown(vacancy_title)}\n\n"
            f"🤖 Анализ GigaChat:\n"
            f"📄 Оценка резюме: *{escape_markdown(resume_score)}*\n"
            f"⭐ Оценка ответов в Telegram: *{escape_markdown(telegram_score)}*\n\n"
            f"⚙️ Решение GigaChat: {bold(escape_markdown(decision))}\n\n"
            f"📅 Оценка получена: {escape_markdown(date)}\n\n"
            f"🔄 Статус по обработке от HR: {bold(escape_markdown(status))}\n\n"
            + hr_info
    )

def candidate_answers_message(
    answers: str
) -> str:
    return (
        f"📝 Ответы кандидата:\n\n{answers}"
    )


NOT_REGISTERED_AS_HR = (
    "⚠️ Вы не зарегистрированы как HR-специалист.\n"
    "Если вы желаете зарегистрироваться как HR, запросите "
    "токен регистрации у вашего администратора и выполните "
    "команду */register_hr*"
)

WORK_MODE_CHANGE_CANCELLED = (
    "❌ Изменение режима работы отменено пользователем"
)

HR_MENU_SELECT = (
    "🔍 Выберите необходимое меню"
)

EMPTY_REVIEWS = (
    "❌ Ни одного нового решения ещё не вынесено"
)

NEW_REVIEWS_BUTTON = '🆕 Новые решения'

PROCESSING_REVIEWS_BUTTON = "⏳ В обработке"

ARCHIVE_REVIEWS_BUTTON = "🗄 Архив решений"
ARCHIVE_TYPE_CHOOSE = "🗄 Выберите тип архива:"
ARCHIVE_APPROVED = "📁 Архив: Одобренные кандидаты"
ARCHIVE_DECLINED = "📁 Архив: Отклоненные кандидаты"

NEW_REVIEWS = (
    "🆕 Новые решения по кандидатам:"
)

PROCESSING_REVIEWS = (
    "⏳ Решения в обработке:"
)

ARCHIVE_REVIEWS = (
    "🗄 Архив решений по кандидатам:"
)

GET_CANDIDATE_ANSWERS = (
    "📝 Посмотреть ответы"
)

GET_CANDIDATE_RESUME = (
    "📄 Посмотреть резюме"
)

REVIEW_NOT_FOUND = (
    "❌ Решение не найдено"
)

TAKE_TO_PROCESSING = (
    "🛠 Взять в обработку"
)

REVIEW_APPROVED = (
    "✅ Одобрено"
)

REVIEW_DECLINED = (
    "❌ Отказано"
)

NO_RESUME_FOR_REVIEW = (
    "Резюме для этого кандидата не найдено"
)

MARK_REVIEW_AS_PROCESSING = (
    "✅ Взято в обработку"
)

MARK_REVIEW_AS_ACCEPTED = (
    "✅ Кандидат одобрен"
)

MARK_REVIEW_AS_DECLINED = (
    "❌ Кандидат отклонен"
)

TO_ACCEPTED_CANDIDATE = (
    "Благодарим за интерес к данной вакансии.\n\n"
    "🎉 В этом сообщении мы ещё раз подтверждаем, что "
    "ваша кандидатура подходит по нашим требованиям!"
)

TO_DECLINED_CANDIDATE = (
    "Благодарим за интерес к данной вакансии.\n\n"
    "😔 К сожалению, на текущий момент мы сделали выбор в "
    "пользу другого кандидата. Вы можете откликнуться на "
    "другие вакансии Сбербанка"
)

#-----------------
# Constants used in hr_registration.py
#-----------------
def hr_registered_message(hr_full_name: str) -> str:
    return (
        "✅ Регистрация успешно завершена!\n\n"
        f"*Добро пожаловать, {hr_full_name}!*\n"
        "Для вызова меню решений по кандидатам, воспользуйтесь командой */get_reviews*"
    )

def hr_registered_notification_message(
    hr_full_name: str,
    telegram_id: str    
) -> str:
    return (
        f"*🆕 Новый HR зарегистрирован: *"
        f"[{hr_full_name}](tg://user?id={telegram_id})\n"
        f"ID: `{telegram_id}`"
    )


HR_ALREADY_EXISTS = (
    "⚠️ Вы уже зарегистрированы как HR-специалист!\n\n"
    f"Для вызова меню решений по кандидатам, воспользуйтесь командой */get_reviews*\n\n"
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


#-----------------
# Constants used in admin_screening_commands.py
#-----------------
def _screening_info_message(
    is_for_screening: bool,
    screening_cretiria: str
) -> str:
    screening_info = (
                f"\n\n🤖 Промпт для вопроса:\n{screening_cretiria}"
                if is_for_screening and screening_cretiria
                else "\n\n🤖 Промпт не настроен"
            )
    return screening_info


def _choices_info_message(
    choices 
) -> str:
    choices_info = ("Варианты ответов:\n" + " | ".join(choices)) if choices else ""
    return choices_info


def vacancy_question_detail_message(
    question_order: Optional[int],
    question_text: Optional[str],
    choices,
    is_for_screening: Optional[bool],
    screening_criteria: Optional[str]
) -> str:
    detail_text = (
        f"📝 Вопрос №{question_order}:\n\n"
        f"{question_text}"
        f"\n{_choices_info_message(choices)}"
        f"{_screening_info_message(
            is_for_screening, 
            screening_criteria
            )}"
    )
    return detail_text


def vacancy_detail_message(
    title: str,
    description: str,
    all: int,
    active: int,
    review: int,
    approved: int,
    declined: int
) -> str:
    detail_text = (
        f"📌 Вакансия:\n{title}\n\n"
        f"📝 Описание вакансии:\n{description}\n\n"
        f"📅 Всего откликов в системе: {all}\n"
        f"🔍 Ещё не прошли опросник: {active}\n"
        f"⏳ Откликов в обработке: {review}\n"
        f"✅ Одобренных откликов: {approved}\n"
        f"❌ Отклоненных откликов: {declined}"
    )
    return detail_text


def edit_prompt_message(criteria: str) -> str:
    return (
        f"Текущий промпт для вопроса:\n\n{criteria}\n\n"
        f"{PROMPT_CREATE_HELPER}"
        "🤖 *Введите новый промпт:*"
    )


def edit_question_text_message(text: str) -> str:
    return (
        f"Текущий текст вопроса:\n\n{text}\n\n"
        "Введите новый текст вопроса:"
    )


def edit_choices_message(choices) -> str:
    return (
        f"Текущие варианты ответов:\n\n{' | '.join(choices)}\n\n"
        "❗️Введите новые варианты ответов, *через запятую (регистр не имеет значение)*\n\n"
        "*Пример:* 'полный день, гибкий график, удаленная работа' - распознается как 3 варианта ответа"
    )


PROMPT_CREATE_HELPER = (
    "Внимательно ознакомьтесь с памяткой ниже!\n"
    "*Памятка:* ваш промпт должен ставить задачу оценивания ответа на вопрос от кандидата. "
    "Он так же обязательно должен содержать правила оценивания ответа *(указание цельного числа баллов за ответ)*.\n\n"
    "Например:\n❓ *Вопрос:* 'Почему вы считаете работу в контактном центре стрессовой?'\n"
    "🤖 *Вариант промпта:* Оцени ответ кандидата: если ответ общий, без объяснений или просто согласие/несогласие без аргументов — ставь 0; " 
    "если приведено одно простое или поверхностное объяснение (например, из-за клиентов или нагрузки), но без раскрытия — ставь 5; если ответ развернутый, " 
    "с конкретными причинами (например, эмоциональное выгорание, высокая нагрузка, конфликтные ситуации), логикой и пониманием специфики работы — ставь 10.\n\n"
)

CREATE_NEW_QUESTION = "➕ Создать новый вопрос"
CANCEL_EDIT_VACANCY = "❌ Отменить редактирование"
NO_VACANCIES_IN_SYSTEM = "❌ В системе нет вакансий"
VACANCY_NOT_FOUND = "😔 Вакансия не найдена"
NO_QUESTIONS_FOR_VACANCY = "У данной вакансии нет вопросов"
VACANCIES_LIST = "📋 Список вакансий в системе:"

EDITING_VACANCY_QUESTIONS = "📝 Редактирование вопросов вакансии:"
VIEW_VACANCY_PARAMS = "📝 Просмотреть параметры вакансии"
EDIT_VACANCY_PARAMS = "✏️ Редактировать параметры вакансии"
EDIT_QUESTION_TEXT = "✏️ Редактировать текст вопроса"
EDIT_QUESTION_CHOICES = "✏️ Редактировать варианты ответов"
ADD_QUESTION_CHOICES = "➕ Добавить варианты ответа к вопросу"
EDIT_QUESTION_PROMPT = "🤖 Редактировать промпт для вопроса"
ADD_QUESTION_PROMPT = "➕ Добавить промпт для вопроса"
DELETE_QUESTION_CHOICES = "🗑️ Удалить варианты ответов у вопроса"
DELETE_QUESTION_PROMPT = "🗑️ Удалить промпт для вопроса"
DELETE_QUESTION = "🗑️ Удалить вопрос"
TO_QUESTIONS_LIST = "🔙 Назад к списку вопросов"

TEXT_TYPE = "📝 Текстовый вопрос"
CHOICES_TYPE = "🔘 С вариантами ответа"
CANCEL_QUESTION_CREATION = "❌ Отменить создание"
SAVE_QUESTION = "✅ Сохранить вопрос"
ADD_PROMPT = "🤖 Добавить промпт для скрининга вопроса"
INCORRECT_INPUT_PROVIDED = "Пожалуйста, введите текстовый вопрос"
QUESTION_SAVED = "✅ Вопрос успешно сохранён!"
INCORRECT_QUESTION_OPERATION = "⚠️ Неизвестная операция над вопросом"