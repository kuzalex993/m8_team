"""Resolve a user's Telegram ``chat_id`` and send them a message.

Ported from ``components/admin/notify.py`` and ``userPage.notify_admin``.
"""

from __future__ import annotations

from m8_team.backend.notifications.telegram import TelegramClient
from m8_team.backend.repositories.users_repo import UsersRepo


class NotificationService:
    def __init__(self, users: UsersRepo, telegram: TelegramClient) -> None:
        self._users = users
        self._telegram = telegram

    def notify_user(self, user_id: str, text: str) -> None:
        self._telegram.send_message(self._users.chat_id(user_id), text)

    def notify_admin(self, text: str) -> None:
        self._telegram.send_message(self._users.chat_id("admin"), text)
