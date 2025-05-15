import logging
import src.gigachat_module.utils.prompts as prompts

from typing import Tuple, List

from .client import get_gigachat_client
from langchain_core.messages import SystemMessage, HumanMessage
from src.gigachat_module.parser import ResumeData


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
    
    def _calculate_intermediate_values(self, resume_data: ResumeData) -> Tuple[int, int]:
        age_score = 0
        salary_score = 0
        
        if resume_data.age:
                age = resume_data.age
                if 24 <= age <= 35:
                    age_score = 20
                elif 36 <= age <= 42:
                    age_score = 10
                elif 18 <= age <= 23:
                    age_score = 5
                    
        if resume_data.salary:
            salary = resume_data.salary
            if salary > 60000:
                salary_score = 0
            elif 30000 <= salary <= 60000:
                salary_score = 10
                
        return age_score, salary_score
    
    def _collect_tasks(self, resume_data: ResumeData) -> List[HumanMessage]:
        tasks = []
        resume_data_list = resume_data.to_list()
        try:
            if resume_data.experiences:
                # 11 - индекс experience_summary в ResumeData.to_list() списке
                experience_summary = resume_data_list[11]
                tasks.append(
                    HumanMessage(
                        content=(
                            f'{prompts.WORK_EXPERIENCE_CRITERIA}\n'
                            f'{experience_summary}\n'
                        )
                    )
                )
                if resume_data.skills:
                    # 10 - индекс skills_summary в ResumeData.to_list() списке
                    skills_summary =resume_data_list[10]
                    tasks.append(
                        HumanMessage(
                            content=(
                                f'{prompts.CUSTOMER_FOCUS_CRITERIA}\n'
                                f'{skills_summary}\n'
                                f'{experience_summary}\n'
                        )
                    ))
                    
                    tasks.append(
                        HumanMessage(
                            content=(
                                f'{prompts.COMPUTER_SKILLS_CRITERIA}\n'
                                f'{skills_summary}\n'
                                f'{experience_summary}\n'
                        )
                    ))
                    
                    tasks.append(
                        HumanMessage(
                            content=(
                                f'{prompts.STRESS_RESISTANCE_CRITERIA}\n'
                                f'{skills_summary}\n'
                                f'{experience_summary}\n'
                        )
                    ))
                    
            if resume_data.employment:
                # 12 - индекс employment_summary в ResumeData.to_list() списке
                employment_summary = resume_data_list[12]
                tasks.append(
                    HumanMessage(
                        content=(
                            f'{prompts.SHIFT_WORK_SCHEDULE_EXPERIENCE_CRITERIA}\n'
                            f'{employment_summary}\n'            
                    )
                ))
            
            return tasks
        except Exception as e:
            logger.error(f'Failed to create tasks from ResumeData: {resume_data}. Error: {str(e)}')  
            return []
    
    async def screen_resume(self, resume_data: ResumeData, job_requirements: str = None) -> int:
        """
        Провести оценку резюме кандидата с помощью GigaChat
        
        Args:
            resume_data (ResumeData): Обобщенная информация о резюме кандидата
            job_requirements (str): Специфические требования по вакансии
            
        Returns:
            int: Оценка от GigaChat относительно резюме
        """
        # Общая оценка
        global_score = 0
        
        # Глобальный системный промпт
        system_message = SystemMessage(content=prompts.RESUME_SYSTEM_MESSAGE)
        
        try:
            age_score, salary_score = self._calculate_intermediate_values(resume_data=resume_data)
            global_score += age_score + salary_score
            tasks = self._collect_tasks(resume_data=resume_data)
            
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
            logger.error(f'Failed to invoke tasks: {tasks}. Error: {str(e)}')
            return global_score