"""Domain vocabulary that used to live as magic strings in the UI layer
(``components/admin/constants.py`` and hardcoded literals in ``userPage.py``).

Values are the exact strings persisted in Firestore - do not change them without a
data migration.
"""

from __future__ import annotations

from enum import StrEnum


class TransactionType(StrEnum):
    CHARGE = "charge bonus"
    WRITE_OFF = "write off bonus"
    RESERVE = "reserve bonus"
    DEBIT = "debiting bonus"


class EventType(StrEnum):
    ADMIN = "admin"
    USER_CHALLENGE = "user_challenge"
    USER_REWARD = "user_reward"


class ChallengeStatus(StrEnum):
    NEW = "new"
    ONGOING = "ongoing"
    FINISHED = "finished"


class RewardStatus(StrEnum):
    NEW = "new"
    COMPLETED = "completed"
