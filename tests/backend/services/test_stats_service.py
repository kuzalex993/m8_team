"""Team-membership filtering in the admin stats aggregations.

Former employees are users flagged ``is_active=False`` *and* ids with no ``users`` doc at
all (profile deleted, history left behind in ``user_challenge`` / ``user_bonus``).
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from m8_team.backend.domain.enums import ChallengeStatus, EventType
from m8_team.backend.services.stats_service import (
    ADMIN_SOURCE_COLUMN,
    CHALLENGE_SOURCE_COLUMN,
    OTHER_SOURCE_COLUMN,
    StatsService,
)

DIRECTORY = [
    ("Иван", "ivan", True),
    ("Петр", "petr", False),  # former employee
    ("Админ", "admin", True),  # service account, always excluded
]


@pytest.fixture
def service() -> StatsService:
    users = MagicMock()
    users.employee_directory.return_value = DIRECTORY
    users.employee_map.return_value = {name: uid for name, uid, _ in DIRECTORY}
    return StatsService(MagicMock(), MagicMock(), users)


def _bonus_rows() -> list[dict[str, object]]:
    return [
        {"user_id": "ivan", "bonus_value": 10, "event_type": EventType.USER_CHALLENGE},
        {"user_id": "ivan", "bonus_value": 5, "event_type": EventType.ADMIN},
        {"user_id": "petr", "bonus_value": 30, "event_type": "user_challenge"},  # as persisted
        {"user_id": "ghost", "bonus_value": 5, "event_type": EventType.ADMIN},  # profile deleted
        {"user_id": "admin", "bonus_value": 99, "event_type": EventType.ADMIN},
    ]


def test_bonuses_hide_former_employees_by_default(service: StatsService) -> None:
    totals = service.bonuses_earned_by_user(_bonus_rows())
    assert totals.to_dict("index") == {
        "Иван": {CHALLENGE_SOURCE_COLUMN: 10, ADMIN_SOURCE_COLUMN: 5}
    }


def test_bonuses_include_former_employees_on_request(service: StatsService) -> None:
    totals = service.bonuses_earned_by_user(_bonus_rows(), include_inactive=True)
    # service accounts stay hidden; a deleted profile has no name, so its id is shown
    assert totals.to_dict("index") == {
        "Петр": {CHALLENGE_SOURCE_COLUMN: 30, ADMIN_SOURCE_COLUMN: 0},
        "Иван": {CHALLENGE_SOURCE_COLUMN: 10, ADMIN_SOURCE_COLUMN: 5},
        "ghost": {CHALLENGE_SOURCE_COLUMN: 0, ADMIN_SOURCE_COLUMN: 5},
    }
    assert list(totals.index) == ["Петр", "Иван", "ghost"]  # biggest earners first


def test_bonuses_are_split_by_source(service: StatsService) -> None:
    totals = service.bonuses_earned_by_user(_bonus_rows())
    assert list(totals.columns) == [CHALLENGE_SOURCE_COLUMN, ADMIN_SOURCE_COLUMN]


def test_bonuses_with_unknown_event_type_go_to_other_column(service: StatsService) -> None:
    rows = [
        {"user_id": "ivan", "bonus_value": 10, "event_type": EventType.USER_CHALLENGE},
        {"user_id": "ivan", "bonus_value": 7, "event_type": "legacy"},
    ]
    totals = service.bonuses_earned_by_user(rows)
    assert totals.loc["Иван"].to_dict() == {
        CHALLENGE_SOURCE_COLUMN: 10,
        ADMIN_SOURCE_COLUMN: 0,
        OTHER_SOURCE_COLUMN: 7,
    }


def _challenges_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("ivan", "Иван", ChallengeStatus.FINISHED, True),
            ("petr", "Петр", ChallengeStatus.FINISHED, False),
            ("ghost", "Призрак", ChallengeStatus.FINISHED, True),  # profile deleted
            ("admin", "Админ", ChallengeStatus.FINISHED, True),
        ],
        columns=["user_id", "user_name", "challenge_status", "challenge_success"],
    )


def test_finished_challenges_hide_former_employees_by_default(service: StatsService) -> None:
    counts = service.finished_challenges_by_user(_challenges_df())
    assert list(counts.index) == ["Иван"]


def test_finished_challenges_include_former_employees_on_request(service: StatsService) -> None:
    counts = service.finished_challenges_by_user(_challenges_df(), include_inactive=True)
    assert sorted(counts.index) == ["Иван", "Петр", "Призрак"]
