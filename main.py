from fastapi import FastAPI, HTTPException, Request
from telegram import Bot, Update
import os, json
from dotenv import load_dotenv

from util import get_logger
from chatbot import ask_openai

load_dotenv()
log = get_logger(__name__)

app = FastAPI()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = [7934534604] 
bot = Bot(token=TELEGRAM_TOKEN)

@app.post(f"/chatbot")
async def webhook(request: Request):
    request_json = await request.json()
    log.info(f"Request: {json.dumps(request_json)}")
    update = Update.de_json(request_json, bot)
    user_id = update.message.from_user.id

    if user_id not in ALLOWED_USERS:
        raise HTTPException(status_code=403, detail="Authentication failed")

    user_message = update.message.text
    log.info(f"{user_id} received message of len: {len(user_message)}")
    
    response = await ask_openai(user_id, user_message)
    
    log.info(f"{user_id} sending response of len: {len(response)}")

    sent_message = await bot.send_message(chat_id=user_id, text=response)
    log.info(f"{user_id} created message with id: {sent_message.message_id}")

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')

    uvicorn.run(app, host=host, port=port)