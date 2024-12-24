import os
import requests
from dotenv import load_dotenv
load_dotenv()

GPTSEAL_URL = os.getenv("GPTSEAL_URL")
GPTSEAL_TOKEN = os.getenv("GPTSEAL_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

message = {"update_id": 201856342, "message": {"message_id": 8, "from": {"id": 1, "is_bot": False, "first_name": "X", "language_code": "ru", "is_premium": True}, "chat": {"id": 1, "first_name": "X", "type": "private"}, "date": 1735056409, "text": "Hello there"}}

URL = "http://localhost:8080"
# URL = GPTSEAL_URL

def send_message(user_id: int, user_message: str):
    message["message"]["from"]["id"] = user_id
    message["message"]["chat"]["id"] = user_id
    message["message"]["text"] = user_message
    header = {"Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": GPTSEAL_TOKEN}
    response = requests.post(f"{URL}/chatbot", json=message, headers=header)
    print(response.json())

def setup_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    data = {
        "url": GPTSEAL_URL,
        "secret_token": GPTSEAL_TOKEN
    }

    response = requests.post(url, data=data)
    print(response.text)

if __name__ == "__main__":
    send_message(1, 'tell me a joke')
    # setup_webhook()
