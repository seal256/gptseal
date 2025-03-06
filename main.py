from fastapi import FastAPI, HTTPException, Request
from telegram import Bot, Update
from telegram.constants import MessageLimit
from chatgpt_md_converter import telegram_format
import os, json, asyncio
from dotenv import load_dotenv

from util import format_exception, get_logger
from chatbot import ask_openai

load_dotenv()
log = get_logger('main')

app = FastAPI()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = json.loads(os.getenv("ALLOWED_USERS")) 
GPTSEAL_TOKEN = os.getenv("GPTSEAL_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
user_message_history = {}
MAX_HISTORY_LENGTH = 50
user_tasks: dict[int, asyncio.Task] = {} # TODO: limit the dict growth if there are many users to serve
user_lock = asyncio.Lock()

async def submit_new_message(user_id: int):
    """
    Sends request to openai, records the responce and sends it back to telegram chat.
    """
    try:
        messages = user_message_history.get(user_id, [])
        if not messages:
            log.error(f'{user_id} empty message list')
            return

        response = await ask_openai(user_id, messages)
        log.info(f"{user_id} sending response of len: {len(response)}")

        if len(messages) > MAX_HISTORY_LENGTH:
            messages = messages[-MAX_HISTORY_LENGTH:]
        messages.append({"role": "assistant", "content": response})
        
        async with user_lock:
            user_message_history[user_id] = messages

        html = telegram_format(response)
        if len(html) < MessageLimit.MAX_TEXT_LENGTH:
            sent_message = await bot.send_message(chat_id=user_id, text=html, parse_mode='HTML')
            log.info(f"{user_id} created message with id: {sent_message.message_id}")
        else:
            sent_message = await bot.send_message(chat_id=user_id, text=response[:MessageLimit.MAX_TEXT_LENGTH-5] + '\n...')
            log.info(f"{user_id} created reduced text message with id: {sent_message.message_id}")
        
    except asyncio.CancelledError:
        log.info(f'{user_id} submit_new_message task was cancelled')
    except Exception as e:
        log.error(f'{user_id} error in submit_new_message: {format_exception(e)}')

@app.post("/chatbot")
async def webhook(request: Request):
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != GPTSEAL_TOKEN:
        raise HTTPException(status_code=403, detail="Authentication failed")
    
    request_json = await request.json()
    log.debug(f"Request: {json.dumps(request_json)}")
    update = Update.de_json(request_json, bot)
    user_id = update.message.from_user.id

    if user_id not in ALLOWED_USERS:
        log.info(f'Unknown user {user_id}')
        raise HTTPException(status_code=403, detail="Authentication failed")

    new_user_message = update.message.text
    if not new_user_message:
        log.info(f"{user_id} received invalid update: {update}")
        return {"status": "ok"}
    log.info(f"{user_id} received message of len: {len(new_user_message)}")
    
    async with user_lock: # disallows concurrent requests, but ignores the order of requests
        if user_id not in user_message_history:
            user_message_history[user_id] = []
        message_history = user_message_history.get(user_id)
            
        if user_id in user_tasks:
            if message_history and message_history[-1]['content'] == new_user_message:
                # the message is already processed, nothing to do
                return {"status": "ok"}
            
            else:
                # we need to cancel the existing task
                user_tasks[user_id].cancel()
                await user_tasks[user_id]  # Wait for the task to be cancelled

        if new_user_message == '/new':
            log.info(f"{user_id} clearing message history")
            user_message_history[user_id] = []
            return {"status": "ok"}

        message_history.append({"role": "user", "content": new_user_message})
        task = asyncio.create_task(submit_new_message(user_id))
        user_tasks[user_id] = task
    
    log.info(f'{user_id} submitted new background task')
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')

    uvicorn.run(app, host=host, port=port)