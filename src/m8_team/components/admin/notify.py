"""Telegram notification helper shared by the tabs that need to message an employee
(bonus changes, task assignment, reward confirmation)."""

from m8_team.components.firebase import get_value
from m8_team.components.notifications import send_message

from .constants import USERS_COLLECTION


def notify_user(message: str, user_name: str) -> None:
    user_chat_id = get_value(
        collection_name=USERS_COLLECTION, document_name=user_name, field_name="chat_id"
    )
    send_message(chat_id=user_chat_id, text=message)
