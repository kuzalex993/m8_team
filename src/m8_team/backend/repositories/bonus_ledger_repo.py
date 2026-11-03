"""``user_bonus`` - the append-only bonus transaction ledger, plus the atomic
balance-mutation helpers.

Every balance change goes through one of the ``*_atomic`` methods here: each commits the
ledger row and balance changes together. Reward decisions additionally read and
validate their state inside a Firestore transaction.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

from firebase_admin import firestore
from google.api_core.exceptions import Aborted
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.transaction import Transaction, transactional

from m8_team.backend.domain.clock import DATE_FORMAT, now_iso
from m8_team.backend.domain.enums import EventType, RewardStatus, TransactionType
from m8_team.backend.domain.errors import (
    DomainError,
    InsufficientReservedBonuses,
    InvalidReservation,
    NotFound,
    PersistenceError,
    RewardAlreadyResolved,
)
from m8_team.backend.domain.results import RewardResolution

from .base import BaseRepo
from .collections import USER_BONUS, USER_REWARD, USERS

logger = logging.getLogger(__name__)


class BonusLedgerRepo(BaseRepo):
    def earned_in_range(self, start: date, end: date) -> Iterator[DocumentSnapshot]:
        """``charge bonus`` transactions with ``date`` in [start, end] (inclusive),
        filtered server-side. ``date`` is an ISO-8601 string; a plain ``YYYY-MM-DD``
        bound compares correctly because a prefix sorts before the longer string.
        """
        return self.stream_where(
            USER_BONUS,
            [
                FieldFilter("transaction_type", "==", TransactionType.CHARGE),
                FieldFilter("date", ">=", start.strftime(DATE_FORMAT)),
                FieldFilter("date", "<", (end + timedelta(days=1)).strftime(DATE_FORMAT)),
            ],
        )

    def charge_atomic(
        self,
        *,
        user_id: str,
        transaction_type: str,
        bonus_value: int,
        event_type: str,
        event_id: str | int | None,
    ) -> bool:
        """Append a ledger row and add ``bonus_value`` (may be negative) to
        ``user_free_bonuses`` in one batch."""
        try:
            bonus_ref = self._db.collection(USER_BONUS).document()
            user_ref = self._db.collection(USERS).document(user_id)
            record = {
                "user_id": user_id,
                "transaction_type": transaction_type,
                "bonus_value": bonus_value,
                "event_type": event_type,
                "event_id": event_id,
                "date": now_iso(),
            }
            batch = self._db.batch()
            batch.set(bonus_ref, record)
            batch.update(user_ref, {"user_free_bonuses": firestore.Increment(bonus_value)})
            batch.commit()
            logger.info("Atomic bonus update for '%s': delta=%s", user_id, bonus_value)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Atomic bonus update failed for '%s': %s", user_id, exc)
            return False

    def reserve_atomic(self, *, user_id: str, amount: int, event_id: str | None) -> bool:
        """Move ``amount`` from ``user_free_bonuses`` to ``user_reserved_bonuses`` and log
        a ``reserve bonus`` row - all in one batch."""
        try:
            bonus_ref = self._db.collection(USER_BONUS).document()
            user_ref = self._db.collection(USERS).document(user_id)
            record = {
                "user_id": user_id,
                "transaction_type": TransactionType.RESERVE,
                "bonus_value": amount,
                "event_type": EventType.USER_REWARD,
                "event_id": event_id,
                "date": now_iso(),
            }
            batch = self._db.batch()
            batch.set(bonus_ref, record)
            batch.update(
                user_ref,
                {
                    "user_free_bonuses": firestore.Increment(-amount),
                    "user_reserved_bonuses": firestore.Increment(amount),
                },
            )
            batch.commit()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Atomic reserve failed for '%s': %s", user_id, exc)
            return False

    def _reservation_amount(
        self, transaction: Transaction, *, user_reward_id: str, user_id: str
    ) -> int:
        # Query by request ID first: do not hide corrupt owner/event fields with filters.
        query = self._db.collection(USER_BONUS).where(
            filter=FieldFilter("event_id", "==", user_reward_id)
        )
        records = [
            data
            for doc in transaction.get(query)
            if (data := doc.to_dict()) is not None
            and data.get("transaction_type") == TransactionType.RESERVE
        ]
        if len(records) != 1:
            raise InvalidReservation("expected exactly one reservation")
        record = records[0]
        amount = record.get("bonus_value")
        if (
            record.get("user_id") != user_id
            or record.get("event_type") != EventType.USER_REWARD
            or type(amount) is not int
            or amount <= 0
        ):
            raise InvalidReservation("invalid reservation")
        return amount

    def cancel_reserved_atomic(self, *, user_reward_id: str) -> RewardResolution:
        return self._resolve_reserved_atomic(user_reward_id=user_reward_id, cancel=True)

    def settle_reserved_atomic(self, *, user_reward_id: str) -> RewardResolution:
        return self._resolve_reserved_atomic(user_reward_id=user_reward_id, cancel=False)

    def _resolve_reserved_atomic(self, *, user_reward_id: str, cancel: bool) -> RewardResolution:
        reward_ref = self._db.collection(USER_REWARD).document(user_reward_id)
        # Stable for transaction retries; the ledger row is committed only once.
        bonus_ref = self._db.collection(USER_BONUS).document()

        def resolve(transaction: Transaction) -> RewardResolution:
            reward = reward_ref.get(transaction=transaction).to_dict()
            if reward is None:
                raise NotFound("reward order not found")
            if reward.get("user_reward_status") != RewardStatus.NEW:
                raise RewardAlreadyResolved("reward order already resolved")
            user_id = reward.get("user_id")
            if not isinstance(user_id, str) or not user_id:
                raise InvalidReservation("reward owner missing")
            user_ref = self._db.collection(USERS).document(user_id)
            user = user_ref.get(transaction=transaction).to_dict()
            if user is None:
                raise NotFound("reward owner not found")
            amount = self._reservation_amount(
                transaction, user_reward_id=user_reward_id, user_id=user_id
            )
            reserved = user.get("user_reserved_bonuses")
            free = user.get("user_free_bonuses")
            if type(reserved) is not int or reserved < amount:
                raise InsufficientReservedBonuses
            if cancel and (type(free) is not int or free < 0):
                raise InvalidReservation("invalid free balance")
            balances: dict[str, Any] = {"user_reserved_bonuses": reserved - amount}
            if cancel:
                balances["user_free_bonuses"] = free + amount
            timestamp = now_iso()
            transaction.update(user_ref, balances)
            transaction.update(
                reward_ref,
                {
                    "user_reward_status": RewardStatus.CANCELLED
                    if cancel
                    else RewardStatus.COMPLETED,
                    "user_reward_decision_date": timestamp,
                },
            )
            transaction.create(
                bonus_ref,
                {
                    "user_id": user_id,
                    "transaction_type": TransactionType.REFUND if cancel else TransactionType.DEBIT,
                    "bonus_value": amount,
                    "event_type": EventType.USER_REWARD,
                    "event_id": user_reward_id,
                    "date": timestamp,
                },
            )
            return RewardResolution(user_id, str(reward.get("reward_description", "")), amount)

        try:
            # Release aborted read locks before retrying. Jitter prevents concurrent
            # decisions from repeatedly trying to upgrade the same locks together.
            for attempt in range(5):
                try:
                    result: RewardResolution = transactional(resolve)(
                        self._db.transaction(max_attempts=1)
                    )
                    return result
                except ValueError as exc:
                    if not isinstance(exc.__cause__, Aborted) or attempt == 4:
                        raise
                    time.sleep(random.uniform(0.05, 0.2) * (2**attempt))
            raise AssertionError("unreachable transaction retry state")
        except DomainError:
            raise
        except Exception as exc:
            logger.exception("Reward resolution failed for '%s'", user_reward_id)
            raise PersistenceError("could not resolve reward order") from exc
