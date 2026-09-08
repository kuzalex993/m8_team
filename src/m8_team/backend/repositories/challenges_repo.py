"""``challenges`` collection - the catalogue of assignable tasks."""

from __future__ import annotations

from typing import Any

from .base import BaseRepo
from .collections import CHALLENGES


class ChallengesRepo(BaseRepo):
    def list_all(self) -> list[dict[str, Any]]:
        return self.list_collection(CHALLENGES)

    def add(self, data: dict[str, Any]) -> str | None:
        return self.add_document(CHALLENGES, data)

    def update(self, challenge_id: str, data: dict[str, Any]) -> bool:
        return self.update_document(CHALLENGES, challenge_id, data)

    def reward(self, challenge_id: str) -> Any:
        return self.get_value(CHALLENGES, challenge_id, "challenge_reward")
