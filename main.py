from fastapi import FastAPI, Request
from telegram import Bot, Update
import os
from dotenv import load_dotenv

from util import get_logger
# from chatbot import ask_openai

load_dotenv()
log = get_logger(__name__)

app = FastAPI()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# ALLOWED_USERS = [123456789] 
bot = Bot(token=TELEGRAM_TOKEN)

@app.post(f"/{TELEGRAM_TOKEN}")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), bot)
    user_id = update.message.from_user.id

    # if user_id not in ALLOWED_USERS:
    #     bot.send_message(chat_id=user_id, text="Access denied.")
    #     return {"status": "denied"}

    user_message = update.message.text
    log.info(f"User {user_id} message len: {len(user_message)}")
    
    # response = ask_openai(user_id, user_message)
    response = f'{user_id} said: {user_message}'
    
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=response)
    log.info(f"User {user_id} response len: {len(response)}")

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')

    uvicorn.run(app, host=host, port=port)