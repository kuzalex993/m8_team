import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Function to send message via Telegram bot
def send_message(chat_id, text: str):
    if chat_id is None:
        print(f"chat_id is None - no notifications will be sent!")
        return None
    else:
        url = f"{BASE_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, data=payload)
        return response.json()