"""Default period of the admin stats tab: three calendar months back up to today."""

from __future__ import annotations

from datetime import date

import pytest

from m8_team.ui.admin.tabs.stats import EARLIEST_DATE, default_bonus_range


@pytest.mark.parametrize(
    ("today", "expected_start"),
    [
        (date(2026, 9, 20), date(2026, 6, 20)),
        (date(2026, 1, 15), date(2025, 10, 15)),  # crosses a year boundary
        (date(2026, 5, 31), date(2026, 2, 28)),  # target month is shorter: clamp to month end
        (date(2024, 2, 29), date(2024, 1, 1)),  # never before the earliest selectable date
    ],
)
def test_default_range_is_three_months_back_to_today(today: date, expected_start: date) -> None:
    assert default_bonus_range(today) == (expected_start, today)


def test_default_start_is_never_before_earliest_date() -> None:
    start, _ = default_bonus_range(date(2024, 2, 1))
    assert start == EARLIEST_DATE
