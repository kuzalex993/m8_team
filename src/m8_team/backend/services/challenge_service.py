"""Challenge catalogue CRUD + per-user challenge assignment / completion.

Ports:
- ``components/admin/tasks_tab.py`` add/update
- ``components/admin/employees_tab.py::add_new_user_challenge``
- ``components/userPage.py`` ``add_new_user_challenge`` / ``update_user_challenges_status`` /
  ``close_user_challenge``
"""

from __future__ import annotations

from datetime import date
from typing import Any

from m8_team.backend.domain.clock import now_iso
from m8_team.backend.domain.enums import ChallengeStatus, EventType, TransactionType
from m8_team.backend.domain.models import UserChallenge
from m8_team.backend.domain.results import ChallengeCompletion
from m8_team.backend.domain.rules import completed_on_time
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo
from m8_team.backend.repositories.challenges_repo import ChallengesRepo
from m8_team.backend.repositories.user_challenge_repo import UserChallengeRepo

from .notification_service import NotificationService


class ChallengeService:
    def __init__(
        self,
        challenges: ChallengesRepo,
        user_challenges: UserChallengeRepo,
        ledger: BonusLedgerRepo,
        notifications: NotificationService,
    ) -> None:
        self._challenges = challenges
        self._user_challenges = user_challenges
        self._ledger = ledger
        self._notifications = notifications

    # --- catalogue -------------------------------------------------------

    def list_catalogue(self) -> list[dict[str, Any]]:
        return self._challenges.list_all()

    def add_to_catalogue(self, *, description: str, reward: int, planned_time: int) -> bool:
        return (
            self._challenges.add(
                {
                    "challenge_description": description,
                    "challenge_reward": reward,
                    "challenge_planned_time_completion": planned_time,
                    "challenge_active": True,
                    "challenge_date_update": now_iso(),
                }
            )
            is not None
        )

    def update_catalogue_item(
        self, challenge_id: str, *, description: str, reward: int, planned_time: int
    ) -> bool:
        return self._challenges.update(
            challenge_id,
            {
                "challenge_description": description,
                "challenge_reward": reward,
                "challenge_planned_time_completion": planned_time,
                "challenge_active": True,
                "challenge_date_update": now_iso(),
            },
        )

    # --- assignments ---------------------------------------------------

    def list_all_assignments(self) -> list[dict[str, Any]]:
        return self._user_challenges.list_all()

    def assignments(self, user_id: str, status: str) -> list[UserChallenge]:
        return self._user_challenges.models_by_user_and_status(user_id, status)

    def assign(
        self,
        *,
        user_id: str,
        user_name: str,
        challenge_id: int,
        description: str,
        start_date: date,
        duration: int,
        notify: bool = True,
    ) -> bool:
        assigned = self._user_challenges.assign(
            user_id=user_id,
            user_name=user_name,
            challenge_id=challenge_id,
            description=description,
            start_date=start_date,
            challenge_duration=duration,
            challenge_creation_date=now_iso(),
        )
        if assigned is None:
            return False
        if not notify:
            return True
        self._notifications.notify_user(
            user_id,
            (
                "Вам назначено новое задание:\n"
                f"Описание: {description}\n"
                f"Дата начала: {start_date}\n"
                f"Время на выполнение: {duration} дней"
            ),
        )
        return True

    def activate_new(self, user_challenge_ids: list[str]) -> None:
        for uc_id in user_challenge_ids:
            self._user_challenges.set_status(uc_id, ChallengeStatus.ONGOING)

    def complete(
        self, *, user_challenge_id: str, user_id: str, planned_finish: date
    ) -> ChallengeCompletion:
        on_time = completed_on_time(planned_finish, date.today())
        reward_granted = 0

        if on_time:
            challenge_id = self._user_challenges.challenge_id_of(user_challenge_id)
            reward_granted = int(self._challenges.reward(challenge_id))
            self._ledger.charge_atomic(
                user_id=user_id,
                transaction_type=TransactionType.CHARGE,
                bonus_value=reward_granted,
                event_type=EventType.USER_CHALLENGE,
                event_id=user_challenge_id,
            )

        self._user_challenges.update(
            user_challenge_id,
            {
                "fact_finish_date": now_iso(),
                "challenge_status": ChallengeStatus.FINISHED,
                "challenge_success": on_time,
            },
        )
        return ChallengeCompletion(
            user_challenge_id=user_challenge_id,
            on_time=on_time,
            reward_granted=reward_granted,
        )
