"""``user_challenge`` collection - challenges assigned to a specific user."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import FieldFilter

from m8_team.backend.domain.clock import DATE_FORMAT
from m8_team.backend.domain.enums import ChallengeStatus
from m8_team.backend.domain.models import UserChallenge

from .base import BaseRepo
from .collections import USER_CHALLENGE


class UserChallengeRepo(BaseRepo):
    def list_all(self) -> list[dict[str, Any]]:
        return self.list_collection(USER_CHALLENGE)

    def by_user_and_status(self, user_id: str, status: str) -> Iterator[DocumentSnapshot]:
        return self.stream_where(
            USER_CHALLENGE,
            [
                FieldFilter("user_id", "==", user_id),
                FieldFilter("challenge_status", "==", status),
            ],
        )

    def models_by_user_and_status(self, user_id: str, status: str) -> list[UserChallenge]:
        out: list[UserChallenge] = []
        for doc in self.by_user_and_status(user_id, status):
            data = doc.to_dict()
            if data is None:
                continue
            out.append(UserChallenge.from_dict(data, doc.id))
        return out

    def assign(
        self,
        *,
        user_id: str,
        user_name: str,
        challenge_id: int,
        description: str,
        start_date: date,
        challenge_duration: int,
        challenge_creation_date: str,
    ) -> str | None:
        record = {
            "user_id": user_id,
            "user_name": user_name,
            "challenge_id": challenge_id,
            # Firestore keeps the historical misspelling.
            "challenge_descripion": description,
            "start_date": start_date.strftime(DATE_FORMAT),
            "planned_finish_date": (start_date + timedelta(days=challenge_duration)).strftime(
                DATE_FORMAT
            ),
            "fact_finish_date": None,
            "challenge_status": ChallengeStatus.NEW,
            "challenge_success": "uknonwn",
            "challenge_creation_date": challenge_creation_date,
        }
        return self.add_document(USER_CHALLENGE, record)

    def update(self, user_challenge_id: str, data: dict[str, Any]) -> bool:
        return self.update_document(USER_CHALLENGE, user_challenge_id, data)

    def set_status(self, user_challenge_id: str, status: str) -> bool:
        return self.update_value(USER_CHALLENGE, user_challenge_id, "challenge_status", status)

    def challenge_id_of(self, user_challenge_id: str) -> Any:
        return self.get_value(USER_CHALLENGE, user_challenge_id, "challenge_id")
