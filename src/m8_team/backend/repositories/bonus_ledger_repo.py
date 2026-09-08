"""``user_bonus`` - the append-only bonus transaction ledger, plus the atomic
balance-mutation helpers.

Every balance change goes through one of the ``*_atomic`` methods here: each writes the
ledger row and the balance delta in a single Firestore ``batch`` using
``firestore.Increment``. This replaces the older read-modify-write-in-Python code that
used to live in ``userPage.py`` and ``requests_tab.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import date, timedelta

from firebase_admin import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import FieldFilter

from m8_team.backend.domain.clock import DATE_FORMAT, now_iso
from m8_team.backend.domain.enums import EventType, TransactionType

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

    def settle_reserved_atomic(self, *, user_id: str, amount: int, user_reward_id: str) -> bool:
        """Confirm a reward: drop ``amount`` from ``user_reserved_bonuses``, mark the
        ``user_reward`` completed and log a ``debiting bonus`` row - one batch."""
        try:
            bonus_ref = self._db.collection(USER_BONUS).document()
            user_ref = self._db.collection(USERS).document(user_id)
            reward_ref = self._db.collection(USER_REWARD).document(user_reward_id)
            record = {
                "user_id": user_id,
                "transaction_type": TransactionType.DEBIT,
                "bonus_value": amount,
                "event_type": EventType.USER_REWARD,
                "event_id": user_reward_id,
                "date": now_iso(),
            }
            batch = self._db.batch()
            batch.set(bonus_ref, record)
            batch.update(user_ref, {"user_reserved_bonuses": firestore.Increment(-amount)})
            batch.update(
                reward_ref,
                {
                    "user_reward_status": "completed",
                    "user_reward_decision_date": now_iso(),
                },
            )
            batch.commit()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Atomic settle failed for '%s': %s", user_id, exc)
            return False
