import asyncio

from src.gigachat_module.client import get_gigachat_client
from langchain_core.messages import HumanMessage


def _custom_llm_task(prompt: str) -> str:
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
 
    
async def custom_llm_task_loop():
    while True:
        user_input = await asyncio.to_thread(input, "ПРОМПТ ПОЛЬЗОВАТЕЛЯ: ")
        if user_input.strip().upper() == "СТОП":
            break
        response = await asyncio.to_thread(_custom_llm_task, user_input)
        print(f"GigaChat ответ: {response}")