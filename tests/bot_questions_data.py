TEST_QUESTION_DATA_1 = [
    {
        'question_text': 'вопрос 1',
        'expected_format': 'TEXT',
        'order': 1,
        'choices': None
    },
    {
        'question_text': 'вопрос 2',
        'expected_format': 'TEXT',
        'order': 2,
        'choices': None
    },
    {
        'question_text': 'вопрос с выбором',
        'expected_format': 'CHOICE',
        'order': 3,
        'choices': ["Туда", "Сюда"]
    },
    {
        'question_text': 'ещё вопросик вот с текстом',
        'expected_format': 'TEXT',
        'order': 4,
        'choices': None
    },
    {
       'question_text': 'ещё на выбор ответа',
       'expected_format': 'CHOICE',
       'order': 5,
       'choices': ["шучу, выбора нет"]
    }
]


TEST_QUESTION_DATA_2 = [
    {
       'question_text': 'а тут другие вопросы',
       'expected_format': 'CHOICE',
       'order': 1,
       'choices': ["Круто", "Нифигасе"]
    },
    {
       'question_text': 'и на выбор есть',
       'expected_format': 'CHOICE',
       'order': 2,
       'choices': ["норм", "норм"]
    },
    {
       'question_text': 'Здарова',
       'expected_format': 'CHOICE',
       'order': 3,
       'choices': ["Нет", "Нет"]
    },
    {
       'question_text': 'Ну ещё чтлль один добавить',
       'expected_format': 'CHOICE',
       'order': 4,
       'choices': ["Да", "Нет"]
    },
    {
       'question_text': 'Если ответили "Да" - молодцы',
       'expected_format': 'TEXT',
       'order': 5,
       'choices': None
    }
]


QUESTION_DATA = [
    {
        'question_text': 'Укажите пожалуйста ваше полное Имя Фамилию Отчество?',
        'expected_format': 'TEXT',
        'order': 1,
        'choices': None,
        'is_for_screening': False
    },
    {
        'question_text': 'В каком городе вы проживаете?',
        'expected_format': 'TEXT',
        'order': 2,
        'choices': None,
        'is_for_screening': False
    },
    {
        'question_text': 'Какой формат работы вам интересен?',
        'expected_format': 'CHOICE',
        'order': 3,
        'choices': ["Офис", "Удаленка"],
        'is_for_screening': False
    },
    {
        'question_text': 'Почему именно такой формат вы выбираете, поясните',
        'expected_format': 'TEXT',
        'order': 4,
        'choices': None,
        'is_for_screening': False
    },
    {
       'question_text': 'Сколько вам полных лет?',
       'expected_format': 'CHOICE',
       'order': 5,
       'choices': ["<18", "18-23", "24-35", "36-42", ">42"],
       'is_for_screening': False
    },
    {
       'question_text': 'Есть ли у вас опыт работы в Контактном центре?',
       'expected_format': 'CHOICE',
       'order': 6,
       'choices': ["Да", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Есть ли у вас опыт работы в продажах?',
       'expected_format': 'CHOICE',
       'order': 7,
       'choices': ["Да", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Есть ли у вас опыт работы в сфере услуг?',
       'expected_format': 'CHOICE',
       'order': 8,
       'choices': ["Да", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Считаете ли вы себя клиентоориентированным человеком?',
       'expected_format': 'CHOICE',
       'order': 9,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Если ответили "Да" на предыдущий вопрос: по каким признакам вы считаете себя клиентоориентированным? Приведите пример ситуации, когда вы проявили клиентоориентированность',
       'expected_format': 'TEXT',
       'order': 10,
       'choices': None,
       'is_for_screening': True,
       'screening_criteria': 'Оцени пример по клиентоориентированности: если он развернутый, конкретный, с описанием ситуации, действий кандидата и положительного результата — ставь 10; если пример поверхностный, слабо раскрыт или неполный — ставь 5; если примера нет, он не про клиента или не демонстрирует клиентоориентированность — ставь 0.'
    },
    {
       'question_text': 'Есть ли у вас навык работы на компьютере?',
       'expected_format': 'CHOICE',
       'order': 11,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Какими офисными программами вы владеете?',
       'expected_format': 'TEXT',
       'order': 12,
       'choices': None,
       'is_for_screening': True,
       'screening_criteria': 'Оцени владение офисными программами: если перечислены только базовые программы без уверенного уровня или указано владею офисными программами без деталей — ставь 0; если упомянуты конкретные программы (например, Word, Excel, PowerPoint) с описанием уровня или задач — ставь 5; если перечислены несколько программ с уверенным уровнем, указаны продвинутые функции (например, сводные таблицы, макросы, Google Workspace, CRM-системы) и примеры использования — ставь 10.'
    },
    {
       'question_text': 'Вы считаете себя стрессоустойчивым человеком?',
       'expected_format': 'CHOICE',
       'order': 13,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Согласны ли вы, что работа в контактном центре может быть стрессовой?',
       'expected_format': 'CHOICE',
       'order': 14,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Почему вы так считаете?',
       'expected_format': 'TEXT',
       'order': 15,
       'choices': None,
       'is_for_screening': True,
       'screening_criteria': 'Оцени обоснование кандидата на ответ про то, является ли работа в контактном центре стрессовой: если ответ общий, без объяснений или просто согласие/несогласие без аргументов — ставь 0; если приведено одно простое или поверхностное объяснение (например, из-за клиентов или нагрузки), но без раскрытия — ставь 5; если ответ развернутый, с конкретными причинами (например, эмоциональное выгорание, высокая нагрузка, конфликтные ситуации), логикой и пониманием специфики работы — ставь 10.'
    },
    {
       'question_text': 'Есть ли у вас опыт работы в сменном графике?',
       'expected_format': 'CHOICE',
       'order': 16,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Готовы ли вы работать в графике 2/2 по 12 часов?',
       'expected_format': 'CHOICE',
       'order': 17,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Есть ли у вас возможность работать ранним утром (с 7 утра) или поздним вечером (до 12 ночи)?',
       'expected_format': 'CHOICE',
       'order': 18,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Планируете ли вы отсутствие в ближайшие 2-3 месяца (отпуск/сессия)?',
       'expected_format': 'CHOICE',
       'order': 19,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Вы готовы проходить обучение и повышать свою квалификацию по работе с чатами и банковскими продуктами?',
       'expected_format': 'CHOICE',
       'order': 20,
       'choices': ["Да", "Затрудняюсь ответить", "Нет"],
       'is_for_screening': False
    },
    {
       'question_text': 'Каковы ваши ожидания по заработной плате?',
       'expected_format': 'CHOICE',
       'order': 21,
       'choices': ["от 30 до 60 тысяч", "Затрудняюсь ответить", "более 60 тысяч"],
       'is_for_screening': False
    }
]