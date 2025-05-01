import json
import logging


logger = logging.getLogger(__name__)


def candidate_answers_formatter(responses_json: str) -> str:
    """
    Форматировать ответы кандидата в читаемый вид
    
    Args:
        responses (str): Десериализованная JSON строка с ответами кандидата
    
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
    json_answers = json.loads(responses_json)
    formatted_text = ""
    for question, answer in json_answers.items():
        formatted_text += f"Q: {question}\nA: {answer}\n\n"
    return formatted_text