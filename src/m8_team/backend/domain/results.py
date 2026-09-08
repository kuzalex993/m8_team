"""Typed return values for service use-cases. The UI turns these into ``st.*`` feedback;
services never touch Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BonusChange:
    """Result of a balance mutation via ``bonus_service``."""

    user_id: str
    delta: int
    transaction_type: str


@dataclass(frozen=True)
class ChallengeCompletion:
    user_challenge_id: str
    on_time: bool
    reward_granted: int
