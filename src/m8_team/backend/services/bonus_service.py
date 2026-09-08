"""Admin-initiated balance adjustments. Ported from
``components/admin/employees_tab.py::update_user_bonus``.
"""

from __future__ import annotations

from m8_team.backend.domain.enums import EventType, TransactionType
from m8_team.backend.domain.errors import InsufficientBalance, PersistenceError
from m8_team.backend.domain.results import BonusChange
from m8_team.backend.domain.rules import write_off_allowed
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo

from .notification_service import NotificationService
from .user_service import UserService


class BonusService:
    def __init__(
        self,
        ledger: BonusLedgerRepo,
        users: UserService,
        notifications: NotificationService,
    ) -> None:
        self._ledger = ledger
        self._users = users
        self._notifications = notifications

    def admin_adjust(
        self, *, user_id: str, amount: int, transaction_type: TransactionType
    ) -> BonusChange:
        """``amount`` is a positive magnitude. ``transaction_type`` is CHARGE or WRITE_OFF."""
        if transaction_type == TransactionType.WRITE_OFF:
            balance = self._users.free_bonuses(user_id)
            if balance is None or not write_off_allowed(balance, amount):
                raise InsufficientBalance
            signed = -amount
        else:
            signed = amount

        if not self._ledger.charge_atomic(
            user_id=user_id,
            transaction_type=transaction_type,
            bonus_value=signed,
            event_type=EventType.ADMIN,
            event_id=None,
        ):
            raise PersistenceError("bonus update failed")

        if signed > 0:
            self._notifications.notify_user(user_id, f"Администратор добавил вам {signed} бонусов")
        elif signed < 0:
            self._notifications.notify_user(
                user_id, f"Администратор уменьшил ваш баланс на {signed} бонусов"
            )
        return BonusChange(user_id=user_id, delta=signed, transaction_type=transaction_type)
