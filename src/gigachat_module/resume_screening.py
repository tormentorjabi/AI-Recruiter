import logging
import src.gigachat_module.utils.prompts as prompts

from typing import Optional, Any, List

from .client import get_gigachat_client
from langchain_core.messages import SystemMessage, HumanMessage
from src.gigachat_module.parser import ResumeData

from src.database.models import ResumeScreeningCriteria, ResumeCriteriaField
from src.database.session import Session


logger = logging.getLogger(__name__)

'''
TODO:
    - Перевести скрининг резюме в модульный формат, с управлением через Telegram-бот:
        - Администратор должен иметь возможность выбрать какие поля резюме оценивать
        - Администратор должен иметь возможность указать способ оценивания полей резюме
'''
class ResumeScreening:
    """
    Скрининг резюме кандидата
    
    Methods:
        screen_resume(resume_data):
            Проводит оценку резюме кандидата с помощью GigaChat
    """
    def __init__(self):
        # Инициализируем GigaChat клиент
        self.giga = get_gigachat_client()
    
    async def get_screening_config(self, vacancy_id: int) -> Optional[ResumeScreeningCriteria]:
        with Session() as db:
            return db.query(ResumeScreeningCriteria).filter(
                ResumeScreeningCriteria.vacancy_id == vacancy_id,
                ResumeScreeningCriteria.is_active == True
            ).first()
    
    def _get_resume_field(self, resume_data: ResumeData, field_name: str) -> Any:
        """Get specific field from ResumeData"""
        if field_name == 'skills':
            return resume_data.skills
        elif field_name == 'experiences':
            return resume_data.experiences
        elif hasattr(resume_data, field_name):
            return getattr(resume_data, field_name)
        return None
    
    def _build_prompt(self, template: str, field_value: Any, resume_data: ResumeData) -> str:
        # TODO: Нужно придумать как собирать данные с ResumeData и объединять их с критерием template
        pass
  
    async def screen_resume(self, resume_data: ResumeData, vacancy_id: int) -> int:
        """
        Провести оценку резюме кандидата с помощью GigaChat
        
        Args:
            resume_data (ResumeData): Обобщенная информация о резюме кандидата
            vacancy_id (int): ID вакансии, по которой проводится скрининг
            
        Returns:
            int: Оценка от GigaChat относительно резюме
        """
        # Общая оценка
        global_score = 0
        
        # Глобальный системный промпт
        system_message = SystemMessage(content=prompts.RESUME_SYSTEM_MESSAGE)
        
        config = await self.get_screening_config(vacancy_id)
        if not config:
            logger.warning(f'No screening config for vacancy: {vacancy_id}')
            return global_score
        
        try:
            criteria_field_configs: Optional[List[ResumeCriteriaField]] = config.fields
            for field_config in criteria_field_configs:
                if not field_config.is_active:
                    continue
                
                field_value = self._get_resume_field(resume_data, field_config.resume_field)
                if not field_value:
                    continue
                
                prompt = self._build_prompt(
                    template=field_config.prompt_template,
                    field_value=field_value,
                    resume_data=resume_data
                )
                
                messages = [
                    system_message,
                    HumanMessage(content=prompt)
                ]
                
                response = await self.giga.ainvoke(messages)
                
                try:
                    score = int(response.content) * field_config.weight
                    global_score += score
                except (ValueError, TypeError):
                    logger.error(f'Invalid score response from screening for resume field: {field_config.resume_field}')
            return global_score  
        except Exception as e:
            logger.error(f'Failed to screen resume. Error: {str(e)}')
            return global_score