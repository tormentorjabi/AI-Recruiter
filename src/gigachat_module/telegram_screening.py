import logging
import src.gigachat_module.utils.prompts as prompts

from typing import List
from langchain_core.messages import SystemMessage, HumanMessage

from .client import get_gigachat_client
from src.gigachat_module.utils.formatters import candidate_answers_formatter

logger = logging.getLogger(__name__)

# Ключи для поиска вопросов должны строго совпадать с вопросами по вакансии.
# Данные для этих ключей взяты из списка текущих вопросов по вакансии из: tests/bot_questions_data.py: QUESTION_DATA
CUSTOMER_FOCUS_QUESTION_KEY = 'Если ответили "Да" на предыдущий вопрос: по каким признакам вы считаете себя клиентоориентированным? Приведите пример ситуации, когда вы проявили клиентоориентированность'
SOFTWARE_QUESTION_KEY = 'Какими офисными программами вы владеете?'
STRESS_QUESTION_KEY_PREFIX = 'Согласны ли вы, что работа в контактном центре может быть стрессовой?'
STRESS_QUESTION_KEY = 'Почему вы так считаете?'


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
    
    def _collect_tasks(self, candidate_responses_json: str) -> List[HumanMessage]:
        tasks = []
        focus_key = [CUSTOMER_FOCUS_QUESTION_KEY]
        software_key = [SOFTWARE_QUESTION_KEY]
        stress_key = [STRESS_QUESTION_KEY_PREFIX, STRESS_QUESTION_KEY]

        try:
            focus_answer = candidate_answers_formatter(candidate_responses_json, focus_key)
            if focus_answer:
                tasks.append(HumanMessage(content=(
                    f'{prompts.TG_CUSTOMER_FOCUS_CRITERIA}\n'
                    f'{focus_answer}')))
            
            software_answer = candidate_answers_formatter(candidate_responses_json, software_key)
            if software_answer:
                tasks.append(HumanMessage(content=(
                    f'{prompts.TG_SOFTWARE_CRITERIA}\n'
                    f'{software_answer}')))
            
            stress_answer = candidate_answers_formatter(candidate_responses_json, stress_key)
            if stress_answer:
                tasks.append(HumanMessage(content=(
                    f'{prompts.TG_STRESS_AT_CALLCENTER_CRITERIA}\n'
                    f'{stress_answer}'
                )))

            return tasks
        except Exception as e:
            logger.error(f'Failed to create tasks from candidate responses: {candidate_responses_json}. Error: {str(e)}')  
            return []
    
    async def screen_answers(
        self, 
        candidate_responses_json: str, 
        screening_criterias: str = None
    ) -> str:
        """
        Провести дополнительную оценку кандидата по его ответам из Telegram бота
        
        Args:
            candidate_responses (str): Обобщенные ответы кандидата в JSON формате
            screening_criterias (str): Требования для скрининга
            
        Returns:
            str: Финальная оценка от GigaChat по кандидату
        """
        # criteria_text = self._format_criteria(screening_criterias) if screening_criterias else ""
        
        # Общая оценка
        global_score = 0
        
        # Глобальный системный промпт
        system_message = SystemMessage(content=prompts.TELEGRAM_SYSTEM_MESSAGE)
        
        try:
            tasks = self._collect_tasks(candidate_responses_json)
            
            for task_message in tasks:
                messages = [
                    system_message,
                    task_message
                ]
                response = await self.giga.ainvoke(messages)
                task_score = response.content
                
                try:
                    global_score += int(task_score)
                except (ValueError, TypeError):
                    pass
            return global_score
        
        except Exception as e:
            logger.error(f'Failed to invoke telegram tasks: {tasks}. Error: {str(e)}')
            return global_score