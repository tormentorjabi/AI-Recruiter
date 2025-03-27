from .client import get_gigachat_client
from langchain_core.messages import SystemMessage, HumanMessage

class ResumeScreening:
    """
    Скрининг резюме кандидата.
    
    Methods:
        screen_resume(resume_info):
            Проводит оценку резюме кандидата с помощью GigaChat.
    """
    def __init__(self):
        # Инициализируем GigaChat клиент
        self.giga = get_gigachat_client()
        
    def screen_resume(self, resume_info: str, job_requirements=None) -> str:
        """
        Провести оценки резюме кандидата с помощью GigaChat
        
        Args:
            resume_info (str): Обобщенная информация о резюме кандидата
            job_requirements: Специфические требования по вакансии
            
        Returns:
            str: Оценка от GigaChat относительно резюме
        """
        
        # TODO: 
        # Необходимо завести SystemMessage() с подробным описанием задачи, которая
        # будет поставлена GigaChat в рамках анализа резюме, требования к вакансии
        # можно передать через job_requirements и включить их в SystemMessage()
        # Затем, сообщения собираются в общий messages = [systemMessage, HumanMessage(content=resume_info)]
        # и отправляются на обработку в GigaChat. Результат оценки возвращаем назад.
        pass
    