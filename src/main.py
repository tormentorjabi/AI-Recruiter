import os

from dotenv import load_dotenv
from gigachat_module.client import get_gigachat_client
from langchain_core.messages import HumanMessage, SystemMessage


load_dotenv()


def custom_llm_task(prompt: str) -> str:
    """
    Прямое общение с GigaChat, предполагается только для этапа разработки
    
    Args:
        prompt (str): Промпт для отправки в модель
        
    Returns:
        str: Ответ GigaChat
    """
    try:
        giga = get_gigachat_client()
        
        messages = [
            HumanMessage(content=prompt)
        ]
        
        response = giga.invoke(messages)
        return response.content
    
    except Exception as e:
        print(f'Error occured in direct LLM task: {e}')
        return None
    

while(True):
    user_msg = input("ПРОМПТ ПОЛЬЗОВАТЕЛЯ: ")
    if user_msg == "СТОП":
        break
    response = custom_llm_task(user_msg)
    print(response)
    