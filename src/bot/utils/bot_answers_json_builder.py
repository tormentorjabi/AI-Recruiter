import json
import logging

from src.database.session import Session
from src.database.models import (
    BotQuestion, BotInteraction
)


logger = logging.getLogger(__name__)

def build_json(application_id: int, vacancy_id: int) -> str:
    """
    Собрать JSON с вопросами о ответами кандидата в рамках его отклика на вакансию
    
    Args:
        application_id (int): ID ключ, указывающий на отклик кандидата в БД
        vacancy_id (int): ID ключ, указывающий на вакансию, по которой создан отклик
        
    Returns:
        output_json (str): JSON строка вида:
            {
                "Вопрос": "Ответ1",
                "Вопрос": "Ответ2",
                "Вопрос": "Ответа нет",
                ...
            }
    """
    combined_json = {}
    
    try:
        with Session() as db:
            questions = db.query(BotQuestion).filter_by(
                vacancy_id=vacancy_id
            ).all()
            
            interaction = db.query(BotInteraction).filter_by(
                application_id=application_id
            ).first()

            for question in questions:
                answer = interaction.answers.get(str(question.id), "Нет ответа")
                combined_json[question.question_text] = answer
            
            output_json = json.dumps(combined_json, ensure_ascii=False, indent=4)
            
        return output_json
    except Exception as e:
        logger.error(f"Error build_json: {str(e)}")
        raise