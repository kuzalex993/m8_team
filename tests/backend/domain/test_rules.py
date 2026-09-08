from datetime import date

from m8_team.backend.domain.rules import can_afford, completed_on_time, write_off_allowed


def test_completed_on_time_true_when_before_or_on_planned() -> None:
    planned = date(2024, 5, 1)
    assert completed_on_time(planned, date(2024, 4, 30))
    assert completed_on_time(planned, planned)


def test_completed_on_time_false_when_late() -> None:
    assert not completed_on_time(date(2024, 5, 1), date(2024, 5, 2))


def test_can_afford() -> None:
    assert can_afford(100, 100)
    assert can_afford(101, 100)
    assert not can_afford(99, 100)


def test_write_off_allowed() -> None:
    assert write_off_allowed(50, 50)
    assert not write_off_allowed(49, 50)
