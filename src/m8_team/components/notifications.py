import logging
import os
from typing import Any

import certifi
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(_handler)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def check_telegram_api() -> None:
    url = "https://api.telegram.org"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logger.info("Successfully connected to Telegram API")
        else:
            logger.error(f"Failed to connect to Telegram API, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")


def send_message(chat_id: int | None, text: str) -> Any:
    if chat_id is None:
        logger.warning("chat_id is None - no notifications will be sent!")
        return None
    else:
        url = f"{BASE_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            response = requests.post(url, data=payload, verify=certifi.where())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None
