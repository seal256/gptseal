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

async def ask_openai(user_id, messages: list[dict]):
    try:
        response = await openai_client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        response_content = response.choices[0].message.content
        
    except Exception as e:
        message = format_exception(e)
        log.error(f"{user_id} ask_openai error: {message}")
        response_content = f"ask_openai error: {message}"

    return response_content

if __name__=='__main__':
    import asyncio
    async def test():
        response = await ask_openai(1234, 'hi')
        print(response)
    asyncio.run(test())
