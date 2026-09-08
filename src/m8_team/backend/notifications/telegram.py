"""Telegram Bot API client. Ported from ``components/notifications.py``; the bot token now
comes from :class:`~m8_team.backend.config.Config` instead of a module-level ``os.getenv``.
"""

from __future__ import annotations

import logging
from typing import Any

import certifi
import requests

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, bot_token: str | None) -> None:
        self._token = bot_token

    @property
    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self._token}"

    def send_message(self, chat_id: int | str | None, text: str) -> Any:
        if not self._token:
            logger.warning("BOT_TOKEN is not configured - no notifications will be sent!")
            return None
        if chat_id is None:
            logger.warning("chat_id is None - no notifications will be sent!")
            return None
        try:
            response = requests.post(
                f"{self._base_url}/sendMessage",
                data={"chat_id": chat_id, "text": text},
                verify=certifi.where(),
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error("An error occurred: %s", exc)
            return None
