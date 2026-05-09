from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class User:
    user_email: str
    user_name: str
    user_position: str
    user_role: str
    user_free_bonuses: int = 0
    user_reserved_bonuses: int = 0
    chat_id: str | None = None
    id: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any], doc_id: str | None = None) -> User:
        return cls(
            user_email=d["user_email"],
            user_name=d["user_name"],
            user_position=d["user_position"],
            user_role=d["user_role"],
            user_free_bonuses=d.get("user_free_bonuses", 0),
            user_reserved_bonuses=d.get("user_reserved_bonuses", 0),
            chat_id=d.get("chat_id"),
            id=doc_id or d.get("id"),
        )


@dataclass
class Reward:
    reward_description: str
    reward_price: int
    reward_last_update: str
    id: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any], doc_id: str | None = None) -> Reward:
        return cls(
            reward_description=d["reward_description"],
            reward_price=d["reward_price"],
            reward_last_update=d["reward_last_update"],
            id=doc_id or d.get("id"),
        )


@dataclass
class Challenge:
    challenge_description: str
    challenge_reward: int
    challenge_planned_time_completion: int
    challenge_active: bool
    challenge_date_update: str
    id: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any], doc_id: str | None = None) -> Challenge:
        return cls(
            challenge_description=d["challenge_description"],
            challenge_reward=d["challenge_reward"],
            challenge_planned_time_completion=d["challenge_planned_time_completion"],
            challenge_active=d["challenge_active"],
            challenge_date_update=str(d["challenge_date_update"]),
            id=doc_id or d.get("id"),
        )


@dataclass
class UserChallenge:
    user_id: str
    user_name: str
    challenge_id: int
    challenge_descripion: str  # typo preserved to match Firestore field name
    start_date: str
    planned_finish_date: str
    challenge_status: str
    challenge_success: str | bool
    challenge_creation_date: str
    fact_finish_date: str | None = None
    id: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any], doc_id: str | None = None) -> UserChallenge:
        return cls(
            user_id=d["user_id"],
            user_name=d["user_name"],
            challenge_id=d["challenge_id"],
            challenge_descripion=d["challenge_descripion"],
            start_date=d["start_date"],
            planned_finish_date=d["planned_finish_date"],
            challenge_status=d["challenge_status"],
            challenge_success=d["challenge_success"],
            challenge_creation_date=d["challenge_creation_date"],
            fact_finish_date=d.get("fact_finish_date"),
            id=doc_id or d.get("id"),
        )


@dataclass
class UserBonus:
    user_id: str
    transaction_type: str
    bonus_value: int
    event_type: str
    date: str
    event_id: str | None = None
    id: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any], doc_id: str | None = None) -> UserBonus:
        return cls(
            user_id=d["user_id"],
            transaction_type=d["transaction_type"],
            bonus_value=d["bonus_value"],
            event_type=d["event_type"],
            date=d["date"],
            event_id=d.get("event_id"),
            id=doc_id or d.get("id"),
        )


@dataclass
class UserReward:
    reward_description: str
    reward_id: str
    user_id: str
    user_name: str
    user_reward_request_date: str
    user_reward_status: str
    user_reward_decision_date: str | None = None
    id: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any], doc_id: str | None = None) -> UserReward:
        return cls(
            reward_description=d["reward_description"],
            reward_id=d["reward_id"],
            user_id=d["user_id"],
            user_name=d["user_name"],
            user_reward_request_date=d["user_reward_request_date"],
            user_reward_status=d["user_reward_status"],
            user_reward_decision_date=d.get("user_reward_decision_date"),
            id=doc_id or d.get("id"),
        )
