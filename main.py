from fastapi import FastAPI, HTTPException, Request
from telegram import Bot, Update
from chatgpt_md_converter import telegram_format
import os, json, asyncio
from dotenv import load_dotenv

from util import get_logger
from chatbot import ask_openai, clean_message_history

load_dotenv()
log = get_logger('main')

app = FastAPI()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = json.loads(os.getenv("ALLOWED_USERS")) 
GPTSEAL_TOKEN = os.getenv("GPTSEAL_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
user_locks = {}

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
        raise HTTPException(status_code=403, detail="Authentication failed")

    user_message = update.message.text
    log.info(f"{user_id} received message of len: {len(user_message)}")
    
    lock = user_locks.setdefault(user_id, asyncio.Lock())
    async with lock: # disallows concurrent requests from the same user, but doesn't check the order of requests
        if user_message == '/new':
            log.info(f"{user_id} clearing message history")
            clean_message_history(user_id)
            return {"status": "ok"}
        
        response = await ask_openai(user_id, user_message)
        log.info(f"{user_id} sending response of len: {len(response)}")

        html = telegram_format(response)
        sent_message = await bot.send_message(chat_id=user_id, text=html, parse_mode='HTML')
        log.info(f"{user_id} created message with id: {sent_message.message_id}")

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')

    uvicorn.run(app, host=host, port=port)