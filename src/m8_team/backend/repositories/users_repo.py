"""``users`` collection (document id == username)."""

from __future__ import annotations

import logging
from typing import Any

from m8_team.backend.domain.models import User

from .base import BaseRepo
from .collections import USERS

logger = logging.getLogger(__name__)


class UsersRepo(BaseRepo):
    def all(self) -> dict[str, dict[str, Any]]:
        logger.info("Retrieve users data")
        docs = self._db.collection(USERS).stream()
        return {doc.id: doc.to_dict() for doc in docs}

    def get(self, user_id: str) -> User | None:
        data = self.get_document(USERS, user_id)
        if data is None:
            return None
        return User.from_dict(data, doc_id=user_id)

    def get_raw(self, user_id: str) -> dict[str, Any] | None:
        return self.get_document(USERS, user_id)

    def free_bonuses(self, user_id: str) -> Any:
        return self.get_value(USERS, user_id, "user_free_bonuses")

    def reserved_bonuses(self, user_id: str) -> Any:
        return self.get_value(USERS, user_id, "user_reserved_bonuses")

    def chat_id(self, user_id: str) -> Any:
        return self.get_value(USERS, user_id, "chat_id")

    def create(self, *, email: str, username: str, name: str) -> bool:
        data = {
            "user_email": email,
            "user_free_bonuses": 0,
            "user_name": name,
            "user_position": "сотрудник",
            "user_reserved_bonuses": 0,
            "user_role": "user",
            "chat_id": None,
        }
        return self.set_document(USERS, username, data)

    def update(self, user_id: str, data: dict[str, Any]) -> bool:
        return self.update_document(USERS, user_id, data)
