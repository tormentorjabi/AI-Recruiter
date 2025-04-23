import json
import logging

from .client import get_gigachat_client
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class TelegramScreening:
    """
    Скрининг ответов кандидата, полученных из Telegram бота
    
    Methods:
        conduct_additional_screening(candidate_responses, screening_criterias):
            Проводит оценку кандидата по ответам из Telegram бота
    """
    def __init__(self):
        # Инициализируем GigaChat клиент
        self.giga = get_gigachat_client()
        
    def _format_criteria(self, criteria):
        """
        Форматировать скрининговые критерии в читаемый вид
        
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
    
    def _format_responses(self, responses):
        """
        Форматировать ответы кандидата в читаемый вид
        Format candidate responses into a readable string
        
        Args:
            answers (str): Десериализованная JSON строка с ответами кандидата
        
        Example:
            responses = 
                {
                    "Вопрос": "Ответ1",
                    "Вопрос": "Ответ2",
                    "Вопрос": "Ответа нет",
                    ...
                }
            
            result -> formatted_text = (
                    Ответы кандидата:
                    Q: Вопрос
                    A: Ответ1
                    
                    Q: Вопрос
                    A: Ответ2
                    
                    Q: Вопрос
                    A: Ответа нет
                    ...
                )
        
        Returns:
            str: Отформатированная строка с ответами кандидата
        """
        json_answers = json.loads(responses)
        formatted_text = "Ответы кандидата:\n"
        for question, answer in json_answers.items():
            formatted_text += f"Q: {question}\nA: {answer}\n\n"
        return formatted_text
    
    async def conduct_additional_screening(self, candidate_responses, screening_criterias=None) -> str:
        """
        Провести дополнительную оценку кандидата по его ответам из Telegram бота
        
        Args:
            candidate_responses: Обобщенные ответы кандидата
            screening_criterias: Требования для скрининга
            
        Returns:
            str: Финальная оценка от GigaChat по кандидату
        """
        criteria_text = self._format_criteria(screening_criterias) if screening_criterias else ""
        # system_message = SystemMessage(content=f"""
        # Я отправляю тебе ответы по кандидату и хочу проверить, правильно ли ты их видишь.

        # Ответы придут тебе в формате:
        #     Q: Вопрос
        #     A: Ответ
        
        #     Q: Вопрос2
        #     A: Ответ2
        #     ...
        #     и так далее
            
        # Просмотри их и скажи мне:
        # Какой ответ был у последнего вопроса?
        # """)
        
        system_message = SystemMessage(content=f"""
        Я отправляю тебе ответы кандидатов. Поставь оценку случайным образом от [0.00, 1.00]
        Ограничивайся двумя знаками после запятой.
        В ответе присылай просто оценку в формате: 'X.XX', например '0.60'        
        """)
        responses_text = self._format_responses(candidate_responses)
        
        messages = [
            system_message,
            HumanMessage(content=responses_text)
        ]
        
        try:
            response = self.giga.invoke(messages)
            return response.content
        
        except Exception as e:
            logger.error(f'Error occured in Telegram Screening: {str(e)}')
            raise