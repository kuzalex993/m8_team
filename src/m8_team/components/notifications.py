import requests
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def check_telegram_api():
    url = "https://api.telegram.org"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully connected to Telegram API")
        else:
            print(f"Failed to connect to Telegram API, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def send_message(chat_id, text: str):
    if chat_id is None:
        print(f"chat_id is None - no notifications will be sent!")
        return None
    else:
        url = f"{BASE_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            response = requests.post(url, data=payload, verify=certifi.where())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None





