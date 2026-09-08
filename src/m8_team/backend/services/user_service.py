"""User reads/writes shared by several tabs.

Includes the ``user_free_bonuses`` int-coercion logic moved out of
``components/admin/data.py::get_user_bonus``.
"""

from __future__ import annotations

import logging

from m8_team.backend.domain.constants import EXCLUDED_EMPLOYEE_IDS
from m8_team.backend.domain.models import User
from m8_team.backend.repositories.users_repo import UsersRepo

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, users: UsersRepo) -> None:
        self._users = users

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_raw(self, user_id: str) -> dict[str, object] | None:
        return self._users.get_raw(user_id)

    def create_employee(self, *, email: str, username: str, name: str) -> bool:
        return self._users.create(email=email, username=username, name=name)

    def employee_map(self) -> dict[str, str]:
        """``{user_name: user_id}`` for real employees only."""
        return {
            data["user_name"]: user_id
            for user_id, data in self._users.all().items()
            if user_id not in EXCLUDED_EMPLOYEE_IDS
        }

    def free_bonuses(self, user_id: str) -> int | None:
        """Ported verbatim from ``components/admin/data.py::get_user_bonus`` - int passes
        through, numeric strings are coerced, anything else logs and returns ``None``."""
        raw = self._users.free_bonuses(user_id)
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            try:
                return int(raw)
            except Exception as exc:  # noqa: BLE001 - match original catch-all
                logger.error("Couldn't convert 'user_bonus' to int. Error message: %s", exc)
                return None
        logger.error("'user_bonus' has unsupported type %s", type(raw))
        return None

    def reserved_bonuses(self, user_id: str) -> int | None:
        raw = self._users.reserved_bonuses(user_id)
        return raw if isinstance(raw, int) else None
