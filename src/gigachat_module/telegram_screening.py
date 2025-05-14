import logging
import src.gigachat_module.utils.prompts as prompts

from typing import List
from langchain_core.messages import SystemMessage, HumanMessage

from .client import get_gigachat_client
from src.gigachat_module.utils.formatters import candidate_answers_formatter

from src.database.session import Session
from src.database.models import BotQuestion

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
    
    def _collect_tasks(
        self, 
        candidate_responses_json: str,
        vacancy_id: int,
    ) -> List[HumanMessage]:
        tasks = []

        try:
            with Session() as db:
                # Забираем все вопросы по вакансии, которые помечены для скрининга
                screening_questions = db.query(BotQuestion).filter(
                    BotQuestion.vacancy_id == vacancy_id,
                    BotQuestion.is_for_screening == True
                ).all()

                # Если таких нет, то задач для скрининга нет
                if not screening_questions:
                    return []
                
                # Забираем тексты вопросов, они служат ключами поиска
                question_texts = [q.question_text for q in screening_questions]
                # Забираем промпты параметров скрининга для вопросов
                screening_criterias = [q.screening_criteria for q in screening_questions]
            
            for text, criteria in zip(question_texts, screening_criterias):
                tasks.append(HumanMessage(content=(
                    f'{criteria}\n'
                    f'{candidate_answers_formatter(candidate_responses_json, [text])}'
                )))

            return tasks
        except Exception as e:
            logger.error(f'Failed to create tasks from candidate responses: {candidate_responses_json}. Error: {str(e)}')  
            return []
    
    async def screen_answers(
        self, 
        candidate_responses_json: str,
        vacancy_id: int,
        screening_criterias: str = None
    ) -> str:
        """
        Провести дополнительную оценку кандидата по его ответам из Telegram бота
        
        Args:
            candidate_responses (str): Обобщенные ответы кандидата в JSON формате
            vacancy_id (int): ID вакансии, по которой пройден опрос
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
            tasks = self._collect_tasks(candidate_responses_json, vacancy_id)
            if len(tasks) > 0:
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
            else:
                return global_score
        
        except Exception as e:
            logger.error(f'Failed to invoke telegram tasks: {tasks}. Error: {str(e)}')
            return global_score