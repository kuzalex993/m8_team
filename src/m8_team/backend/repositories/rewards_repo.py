"""``rewards`` collection - the catalogue of orderable rewards."""

from __future__ import annotations

from typing import Any

from .base import BaseRepo
from .collections import REWARDS


class RewardsRepo(BaseRepo):
    def list_all(self) -> list[dict[str, Any]]:
        return self.list_collection(REWARDS)

    def add(self, data: dict[str, Any]) -> str | None:
        return self.add_document(REWARDS, data)

    def update(self, reward_id: str, data: dict[str, Any]) -> bool:
        return self.update_document(REWARDS, reward_id, data)

    def price(self, reward_id: str) -> Any:
        return self.get_value(REWARDS, reward_id, "reward_price")

    def description(self, reward_id: str) -> Any:
        return self.get_value(REWARDS, reward_id, "reward_description")
