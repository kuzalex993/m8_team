"""Ported from the old ``tests/unit/test_admin_page.py``: the ``user_free_bonuses``
int-coercion logic now lives in ``UserService.free_bonuses``.
"""

import logging
from unittest.mock import MagicMock

import pytest

from m8_team.backend.services.user_service import UserService


@pytest.fixture
def users_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(users_repo: MagicMock) -> UserService:
    return UserService(users_repo)


def test_returns_int_directly(users_repo: MagicMock, service: UserService) -> None:
    users_repo.free_bonuses.return_value = 42
    assert service.free_bonuses("user1") == 42


def test_converts_valid_string_to_int(users_repo: MagicMock, service: UserService) -> None:
    users_repo.free_bonuses.return_value = "100"
    assert service.free_bonuses("user1") == 100


def test_invalid_string_logs_and_returns_none(
    users_repo: MagicMock, service: UserService, caplog: pytest.LogCaptureFixture
) -> None:
    users_repo.free_bonuses.return_value = "not_a_number"
    with caplog.at_level(logging.ERROR, logger="m8_team.backend.services.user_service"):
        assert service.free_bonuses("user1") is None
    assert "Couldn't convert 'user_bonus' to int" in caplog.text


def test_unsupported_type_logs_and_returns_none(
    users_repo: MagicMock, service: UserService, caplog: pytest.LogCaptureFixture
) -> None:
    users_repo.free_bonuses.return_value = {"some": "dict"}
    with caplog.at_level(logging.ERROR, logger="m8_team.backend.services.user_service"):
        assert service.free_bonuses("user1") is None
    assert "unsupported type" in caplog.text


def test_none_value_logs_and_returns_none(
    users_repo: MagicMock, service: UserService, caplog: pytest.LogCaptureFixture
) -> None:
    users_repo.free_bonuses.return_value = None
    with caplog.at_level(logging.ERROR, logger="m8_team.backend.services.user_service"):
        assert service.free_bonuses("user1") is None
    assert "unsupported type" in caplog.text


def test_employee_map_excludes_service_accounts(
    users_repo: MagicMock, service: UserService
) -> None:
    users_repo.all.return_value = {
        "alice": {"user_name": "Alice"},
        "admin": {"user_name": "Admin"},
        "alekseik": {"user_name": "Aleksei"},
    }
    assert service.employee_map() == {"Alice": "alice"}


def test_employee_directory_treats_missing_field_as_active(
    users_repo: MagicMock, service: UserService
) -> None:
    users_repo.all.return_value = {
        "old": {"user_name": "Old"},
        "gone": {"user_name": "Gone", "is_active": False},
        "admin": {"user_name": "Admin"},
    }
    directory = service.employee_directory()
    assert ("Old", "old", True) in directory
    assert ("Gone", "gone", False) in directory
    assert all(user_id != "admin" for _, user_id, _ in directory)


def test_employee_map_includes_inactive(users_repo: MagicMock, service: UserService) -> None:
    users_repo.all.return_value = {
        "a": {"user_name": "A"},
        "b": {"user_name": "B", "is_active": False},
    }
    assert service.employee_map() == {"A": "a", "B": "b"}


def test_set_active_delegates(users_repo: MagicMock, service: UserService) -> None:
    users_repo.set_active.return_value = False
    assert service.set_active("u1", False) is False
    users_repo.set_active.assert_called_once_with("u1", False)
