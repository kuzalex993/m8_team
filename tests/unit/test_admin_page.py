import logging
import sys
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

sys.modules.setdefault("streamlit_option_menu", MagicMock())

from m8_team.components.admin.data import get_user_bonus  # noqa: E402


@pytest.fixture
def mock_get_value(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("m8_team.components.admin.data.get_value")


def test_returns_int_directly(mock_get_value: MagicMock) -> None:
    mock_get_value.return_value = 42
    assert get_user_bonus("user1") == 42


def test_converts_valid_string_to_int(mock_get_value: MagicMock) -> None:
    mock_get_value.return_value = "100"
    assert get_user_bonus("user1") == 100


def test_invalid_string_logs_error_and_returns_none(
    mock_get_value: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_get_value.return_value = "not_a_number"
    with caplog.at_level(logging.ERROR, logger="m8_team.components.admin.data"):
        result = get_user_bonus("user1")
    assert result is None
    assert "Couldn't convert 'user_bonus' to int" in caplog.text


def test_unsupported_type_logs_error_and_returns_none(
    mock_get_value: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_get_value.return_value = {"some": "dict"}
    with caplog.at_level(logging.ERROR, logger="m8_team.components.admin.data"):
        result = get_user_bonus("user1")
    assert result is None
    assert "unsupported type" in caplog.text


def test_none_value_logs_error_and_returns_none(
    mock_get_value: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_get_value.return_value = None
    with caplog.at_level(logging.ERROR, logger="m8_team.components.admin.data"):
        result = get_user_bonus("user1")
    assert result is None
    assert "unsupported type" in caplog.text


def test_calls_get_value_with_correct_args(mock_get_value: MagicMock) -> None:
    mock_get_value.return_value = 0
    get_user_bonus("user_abc")
    mock_get_value.assert_called_once_with(
        collection_name="users",
        document_name="user_abc",
        field_name="user_free_bonuses",
    )
