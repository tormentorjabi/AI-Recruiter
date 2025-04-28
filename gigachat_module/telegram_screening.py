from .client import get_gigachat_client
from langchain_core.messages import SystemMessage, HumanMessage

class TelegramScreening:
    """
    Скрининг ответов кандидата, полученных из Telegram бота
    
    Methods:
        conduct_additional_screening(candidate_responses, screening_creterias):
            Проводит дополнительную оценку кандидата по ответам из Telegram бота
    """
    def __init__(self):
        # Инициализируем GigaChat клиент
        self.giga = get_gigachat_client()
        
    def conduct_additional_screening(self, answers: list[str], screening_criterias=None) -> str:
        "С бдшкой ещё не контактировал, поэтому что передовать и оформеление ещё нужно подредачить"

        template = "Оцени ответы кандидата на вопросы. Строго следуй этому формату: {\"Баллы\": <целое число>, \"Причина\": \"<объяснение>\"}"

        ask_q = [   "Оцени пример по клиентоориентированности: если он развернутый, конкретный, с описанием ситуации, действий кандидата и положительного результата — ставь 10; если пример поверхностный, слабо раскрыт или неполный — ставь 5; если примера нет, он не про клиента или не демонстрирует клиентоориентированность — ставь 0.",
                    "Оцени владение офисными программами: если перечислены только базовые программы без уверенного уровня или указано владею офисными программами без деталей — ставь 0; если упомянуты конкретные программы (например, Word, Excel, PowerPoint) с описанием уровня или задач — ставь 5; если перечислены несколько программ с уверенным уровнем, указаны продвинутые функции (например, сводные таблицы, макросы, Google Workspace, CRM-системы) и примеры использования — ставь 10.",
                    "Ответ на вопрос:Согласны ли вы , что работа в контактном центре может быть срессовой ? Оцени обоснование: если ответ общий, без объяснений или просто согласие/несогласие без аргументов — ставь 0; если приведено одно простое или поверхностное объяснение (например, из-за клиентов или нагрузки), но без раскрытия — ставь 5; если ответ развернутый, с конкретными причинами (например, эмоциональное выгорание, высокая нагрузка, конфликтные ситуации), логикой и пониманием специфики работы — ставь 10.",
                    ]
        p_customer_focus = "\n".join([template, ask_q[0], answers[0]])
        p_programs = "\n".join([template, ask_q[1], answers[1]])
        p_computer = "\n".join([template, ask_q[2], answers[2]])
        asks = [p_customer_focus, p_programs, p_computer]
        answers = []
        try:
            for ask in asks:
                messages = [
                    HumanMessage(content=ask)
                ]
                    
                response = self.giga.invoke(messages, temperature=0)
                answers.append(response.content)
            return answers
            
        except Exception as e:
            print(f'Error occured in direct LLM task: {e}')
            return None
        # TODO: 
        # Необходимо завести SystemMessage() с подробным описанием задачи, которая
        # будет поставлена GigaChat в рамках анализа ответов, требования к анализу
        # можно передать через screening_criterias и включить их в SystemMessage()
        # Затем, сообщения собираются в общий messages = [systemMessage, HumanMessage(content=candidate_responses)]
        # и отправляются на обработку в GigaChat. Результат оценки возвращаем назад.
        pass
    