import json
import logging

from typing import List, Optional, Dict


logger = logging.getLogger(__name__)

def candidate_answers_formatter(
    responses_json: str, 
    keys: Optional[List[str]] = None,
    *,
    question_prefix: str = "Q: ",
    answer_prefix: str = "A: ",
    delimiter: str = "\n\n"
) -> str:
    """
    Форматировать ответы кандидатов из JSON в читаемый текстовый вид.
    
    Args:
        responses_json (str): Десериализованная JSON строка с ответами кандидата
        keys (List[str]): Список ключей вопросов для фильтрации ответов (регистр не учитывается). Если ключи не указаны,
    в результирующую строку включаются все вопросы.
        question_prefix (str): Префикс для вопросов ("Q: " по умолчанию)
        answer_prefix (str): Префикс для ответов ("A: " по умолчанию)
        delimiter (str): Разделитель между парами Q&A ("\\n\\n" по умолчанию)
    
    Returns:
        str: Отформатированная строка с ответами кандидата
    
    Example:
        >>> responses = '{"Вопрос1": "Ответ1", "Вопрос2": "Ответ2"}, "Вопрос3": "Ответ3"}'
        >>> candidate_answers_formatter(responses, keys=["Вопрос1", "Вопрос2"])
        "Q: Вопрос1\\nA:Ответ1\\n\\nQ: Вопрос2\\nA:Ответ2"
    """
    try:
        answers: Dict[str, str] = json.loads(responses_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        return ""
    
    if not answers:
        return ""
    
    normalized_keys = {k.strip().lower() for k in keys} if keys else None
    
    result = []
    for question, answer in answers.items():
        if normalized_keys is None or question.strip().lower() in normalized_keys:
            result.append(
                f"{question_prefix}{question}\n{answer_prefix}{answer}"
            )
    return delimiter.join(result)