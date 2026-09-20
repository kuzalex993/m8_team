"""Shared fixtures for headless UI tests.

The UI is exercised with :class:`streamlit.testing.v1.AppTest` - no browser, no Firebase.
``m8_team.ui.container.get_container`` reads ``st.session_state["container"]``, so seeding that
key with a fake :class:`Container` replaces the whole backend.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from m8_team.backend.domain.enums import ChallengeStatus, RewardStatus
from m8_team.backend.domain.models import UserChallenge, UserReward

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "c1",
        "challenge_description": "Написать пост",
        "challenge_reward": 10,
        "challenge_planned_time_completion": 3,
        "challenge_active": True,
        "challenge_date_update": "2025-01-01T10:00:00.000000Z",
    },
    {
        "id": "c2",
        "challenge_description": "Снять ролик",
        "challenge_reward": 25,
        "challenge_planned_time_completion": 7,
        "challenge_active": True,
        "challenge_date_update": "2025-01-02T10:00:00.000000Z",
    },
]

REWARDS: list[dict[str, Any]] = [
    {
        "id": "r1",
        "reward_description": "Выходной день",
        "reward_price": 100,
        "reward_last_update": "2025-01-01T10:00:00.000000Z",
    },
    {
        "id": "r2",
        "reward_description": "Кофе",
        "reward_price": 15,
        "reward_last_update": "2025-01-02T10:00:00.000000Z",
    },
]

ASSIGNMENTS: list[dict[str, Any]] = [
    {
        "user_id": "ivan",
        "user_name": "Иван",
        "challenge_descripion": "Написать пост",
        "start_date": "2025-01-01",
        "planned_finish_date": "2025-01-04",
        "challenge_status": "ongoing",
        "fact_finish_date": None,
        "challenge_success": "",
    }
]

USER_DATA: dict[str, Any] = {
    "user_name": "Иван",
    "user_position": "SMM",
    "user_free_bonuses": 120,
    "user_reserved_bonuses": 10,
}


@pytest.fixture
def container() -> MagicMock:
    """A fake backend ``Container`` whose services return small, realistic fixtures."""
    c = MagicMock()
    c.config.bot_endpoint = "https://t.me/test_bot"

    # ``cache.challenges_df`` mutates the rows it gets, so hand out fresh copies each call.
    c.challenge.list_catalogue.side_effect = lambda: [dict(r) for r in CHALLENGES]
    c.challenge.list_all_assignments.side_effect = lambda: [dict(r) for r in ASSIGNMENTS]
    c.reward.list_catalogue.side_effect = lambda: [dict(r) for r in REWARDS]

    c.user.employee_map.return_value = {"Иван": "ivan"}
    c.user.employee_directory.return_value = [("Иван", "ivan", True)]
    c.user.free_bonuses.return_value = 120
    c.user.get_raw.side_effect = lambda _user_id: dict(USER_DATA)

    c.reward.requests.return_value = [
        UserReward(
            reward_description="Кофе",
            reward_id="r2",
            user_id="ivan",
            user_name="Иван",
            user_reward_request_date="2025-01-03T09:30:00.000000Z",
            user_reward_status=RewardStatus.NEW,
            id="ur1",
        ),
        UserReward(
            reward_description="Выходной день",
            reward_id="r1",
            user_id="ivan",
            user_name="Иван",
            user_reward_request_date="2025-01-01T09:30:00.000000Z",
            user_reward_status=RewardStatus.COMPLETED,
            user_reward_decision_date="2025-01-02T09:30:00.000000Z",
            id="ur2",
        ),
    ]

    c.stats.finished_challenges_by_user.return_value = pd.DataFrame(
        {"Успешно": [2], "Неуспешно": [1]}, index=["Иван"]
    )
    c.stats.bonuses_earned_by_user.return_value = pd.DataFrame(
        {"challenges": [20], "admin": [10]}, index=["Иван"]
    )
    c.stats.earned_bonus_rows.return_value = []
    return c


@pytest.fixture
def ongoing_challenge() -> UserChallenge:
    return UserChallenge(
        user_id="ivan",
        user_name="Иван",
        challenge_id=1,
        description="Написать пост",
        start_date="2025-01-01",
        planned_finish_date="2025-01-05",
        challenge_status=ChallengeStatus.ONGOING,
        challenge_success="",
        challenge_creation_date="2025-01-01T10:00:00.000000Z",
        id="uc1",
    )


@pytest.fixture
def make_app(container: MagicMock) -> Callable[..., AppTest]:
    """Build an ``AppTest`` around a function or script file with the fake container seeded."""

    def _make(app: Callable[[], None] | str, *, session: dict[str, Any] | None = None) -> AppTest:
        at = (
            AppTest.from_file(app, default_timeout=30)
            if isinstance(app, str)
            else AppTest.from_function(app, default_timeout=30)
        )
        at.session_state["container"] = container
        for key, value in (session or {}).items():
            at.session_state[key] = value
        return at

    return _make


@pytest.fixture
def user_session() -> dict[str, Any]:
    """Session state the user pages expect after login."""
    return {"user_id": "ivan", "username": "ivan", "user_data": dict(USER_DATA)}


@pytest.fixture
def find() -> Callable[[Any, str], Any]:
    """Look up a widget in an AppTest widget list by its label."""

    def _find(elements: Any, label: str) -> Any:
        matches = [el for el in elements if getattr(el, "label", None) == label]
        assert matches, f"no widget labelled {label!r}; have {[e.label for e in elements]}"
        return matches[0]

    return _find
