from .client import get_gigachat_client
from langchain_core.messages import SystemMessage, HumanMessage

class TelegramScreening:
    """
    Скрининг ответов кандидата, полученных из Telegram бота
    
    Methods:
        conduct_additional_screening(candidate_responses, screening_criterias):
            Проводит дополнительную оценку кандидата по ответам из Telegram бота
    """
    def __init__(self):
        # Инициализируем GigaChat клиент
        self.giga = get_gigachat_client()
        
    def _format_criteria(self, criteria):
        """
        Форматировать скрининговые критерии в удовлетворимый вид
        
        Args:
            criteria (dict): Словарь критериев
        
        Example:
            criteria = 
            {
                'навыки_коммуникации': 'Ясные и четкие ответы',
                'технические_познания': 'Продемонстрированы навыки решения проблем'
            } 
            
            result -> criteria_text = (
                    - Навыки Коммуникации: Ясные и четкие ответы
                    - Технические Познания: Продемонстрированы навыки решения проблем
                )

        Returns:
            str: Текст форматированных критериев
        """
        criteria_text = ""
        for key, value in criteria.items():
            criteria_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        return criteria_text
    
    def conduct_additional_screening(self, candidate_responses, screening_criterias=None) -> str:
        """
        Провести дополнительную оценку кандидата по его ответам из Telegram бота
        
        Args:
            candidate_responses: Обобщенные ответы кандидата
            screening_criterias: Требования для скрининга
            
        Returns:
            str: Финальная оценка от GigaChat по кандидату
        """
        
        # TODO: 
        # Необходимо завести SystemMessage() с подробным описанием задачи, которая
        # будет поставлена GigaChat в рамках анализа ответов, требования к анализу
        # можно передать через screening_criterias и включить их в SystemMessage()
        # Затем, сообщения собираются в общий messages = [systemMessage, HumanMessage(content=candidate_responses)]
        # и отправляются на обработку в GigaChat. Результат оценки возвращаем назад.
        pass
    