from openai import AsyncOpenAI
import os
from util import format_exception, get_logger
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = 'gpt-4o-mini'

global openai_client
openai_client = AsyncOpenAI(api_key = OPENAI_API_KEY)
log = get_logger(__name__)

message_history = {}
MAX_HISTORY_LENGTH = 50

def clean_message_history(user_id):
    if user_id in message_history:
        message_history[user_id] = []

async def ask_openai(user_id, user_message: str):
    try:
        messages = message_history.get(user_id, [])
        messages.append({"role": "user", "content": user_message})
        response = await openai_client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        response_content = response.choices[0].message.content

        if user_id not in message_history:
            message_history[user_id] = []
        messages.append({"role": "assistant", "content": response_content})
        if len(messages) > MAX_HISTORY_LENGTH:
            messages = messages[-MAX_HISTORY_LENGTH:]
        message_history[user_id] = messages
        
    except Exception as e:
        message = format_exception(e)
        log.error(f"ask_openai error: {message}")
        response_content = f"ask_openai error: {message}"

    return response_content

if __name__=='__main__':
    import asyncio
    async def test():
        response = await ask_openai(1234, 'hi')
        print(response)
    asyncio.run(test())
