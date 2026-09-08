"""``user_reward`` collection - reward requests raised by users."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import FieldFilter

from m8_team.backend.domain.models import UserReward

from .base import BaseRepo
from .collections import USER_REWARD


class UserRewardRepo(BaseRepo):
    def by_user(self, user_id: str) -> Iterator[DocumentSnapshot]:
        if user_id == "all":
            return self.stream_all(USER_REWARD)
        return self.stream_where(USER_REWARD, [FieldFilter("user_id", "==", user_id)])

    def models_by_user(self, user_id: str) -> list[UserReward]:
        out: list[UserReward] = []
        for doc in self.by_user(user_id):
            data = doc.to_dict()
            if data is None:
                continue
            out.append(UserReward.from_dict(data, doc.id))
        return out

    def create(self, data: dict[str, Any]) -> str | None:
        return self.add_document(USER_REWARD, data)

    def update(self, user_reward_id: str, data: dict[str, Any]) -> bool:
        return self.update_document(USER_REWARD, user_reward_id, data)
