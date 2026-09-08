"""Reward catalogue CRUD + reward request / confirmation.

Ports:
- ``components/admin/rewards_tab.py`` add/update
- ``components/userPage.py::request_reward``
- ``components/admin/requests_tab.py::confirm_user_request``
"""

from __future__ import annotations

from typing import Any

from m8_team.backend.domain.clock import now_iso
from m8_team.backend.domain.enums import RewardStatus
from m8_team.backend.domain.errors import (
    InsufficientBalance,
    InsufficientReservedBonuses,
    PersistenceError,
)
from m8_team.backend.domain.models import UserReward
from m8_team.backend.domain.rules import can_afford
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo
from m8_team.backend.repositories.rewards_repo import RewardsRepo
from m8_team.backend.repositories.user_reward_repo import UserRewardRepo

from .notification_service import NotificationService
from .user_service import UserService


class RewardService:
    def __init__(
        self,
        rewards: RewardsRepo,
        user_rewards: UserRewardRepo,
        users: UserService,
        ledger: BonusLedgerRepo,
        notifications: NotificationService,
    ) -> None:
        self._rewards = rewards
        self._user_rewards = user_rewards
        self._users = users
        self._ledger = ledger
        self._notifications = notifications

    # --- catalogue -------------------------------------------------------

    def list_catalogue(self) -> list[dict[str, Any]]:
        return self._rewards.list_all()

    def add_to_catalogue(self, *, description: str, price: int) -> bool:
        return (
            self._rewards.add(
                {
                    "reward_description": description,
                    "reward_price": price,
                    "reward_last_update": now_iso(),
                }
            )
            is not None
        )

    def update_catalogue_item(self, reward_id: str, *, description: str, price: int) -> bool:
        return self._rewards.update(
            reward_id,
            {
                "reward_description": description,
                "reward_price": price,
                "reward_last_update": now_iso(),
            },
        )

    # --- requests -----------------------------------------------------

    def requests(self, user_id: str = "all") -> list[UserReward]:
        return self._user_rewards.models_by_user(user_id)

    def request(
        self,
        *,
        user_id: str,
        user_name: str,
        reward_id: str,
        reward_description: str,
        reward_price: int,
    ) -> None:
        free = self._users.free_bonuses(user_id)
        if free is None or not can_afford(free, reward_price):
            raise InsufficientBalance

        user_reward_id = self._user_rewards.create(
            {
                "reward_description": reward_description,
                "reward_id": reward_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_reward_decision_date": None,
                "user_reward_request_date": now_iso(),
                "user_reward_status": RewardStatus.NEW,
            }
        )
        if user_reward_id is None:
            raise PersistenceError("could not create reward request")

        if not self._ledger.reserve_atomic(
            user_id=user_id, amount=reward_price, event_id=user_reward_id
        ):
            raise PersistenceError("could not reserve bonuses")

        self._notifications.notify_admin(
            f"Запрошена новая награда:\nПользователь: {user_name}\nНаграда: {reward_description}"
        )

    def confirm(self, *, user_reward_id: str, user_id: str, reward_id: str) -> None:
        price = int(self._rewards.price(reward_id))
        description = self._rewards.description(reward_id)
        reserved = self._users.reserved_bonuses(user_id)
        if reserved is None or price > reserved:
            raise InsufficientReservedBonuses

        if not self._ledger.settle_reserved_atomic(
            user_id=user_id, amount=price, user_reward_id=user_reward_id
        ):
            raise PersistenceError("could not settle reserved bonuses")

        self._notifications.notify_user(user_id, f"Ура! Админ подтвердил награду: {description}")
