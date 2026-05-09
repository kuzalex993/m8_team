from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from m8_team.components.firebase import update_user_bonus_atomic


@pytest.fixture
def mock_db(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("m8_team.components.firebase.db")


@pytest.fixture
def mock_increment(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("m8_team.components.firebase.firestore.Increment")


def test_success_returns_true(mock_db: MagicMock, mock_increment: MagicMock) -> None:
    result = update_user_bonus_atomic(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=500,
        event_type="admin",
        event_id=None,
    )
    assert result is True


def test_batch_is_committed(mock_db: MagicMock, mock_increment: MagicMock) -> None:
    update_user_bonus_atomic(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=500,
        event_type="admin",
        event_id=None,
    )
    mock_db.batch.return_value.commit.assert_called_once()


def test_bonus_record_fields(mock_db: MagicMock, mock_increment: MagicMock) -> None:
    update_user_bonus_atomic(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=500,
        event_type="admin",
        event_id=42,
    )
    batch = mock_db.batch.return_value
    batch.set.assert_called_once()
    _ref, record = batch.set.call_args.args
    assert record["user_id"] == "user123"
    assert record["bonus_value"] == 500
    assert record["transaction_type"] == "charge bonus"
    assert record["event_type"] == "admin"
    assert record["event_id"] == 42
    assert "date" in record


def test_user_balance_incremented(mock_db: MagicMock, mock_increment: MagicMock) -> None:
    mock_user_ref = MagicMock()

    def _collection_side(name: str) -> MagicMock:
        coll = MagicMock()
        if name == "users":
            coll.document.return_value = mock_user_ref
        return coll

    mock_db.collection.side_effect = _collection_side

    update_user_bonus_atomic(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=500,
        event_type="admin",
        event_id=None,
    )

    mock_increment.assert_called_once_with(500)
    mock_db.batch.return_value.update.assert_called_once_with(
        mock_user_ref,
        {"user_free_bonuses": mock_increment.return_value},
    )


def test_commit_failure_returns_false(mock_db: MagicMock, mock_increment: MagicMock) -> None:
    mock_db.batch.return_value.commit.side_effect = Exception("Firestore unavailable")

    result = update_user_bonus_atomic(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=500,
        event_type="admin",
        event_id=None,
    )

    assert result is False


def test_negative_bonus_passes_negative_to_increment(
    mock_db: MagicMock, mock_increment: MagicMock
) -> None:
    result = update_user_bonus_atomic(
        user_id="user123",
        transaction_type="write off bonus",
        bonus_value=-200,
        event_type="admin",
        event_id=None,
    )

    assert result is True
    mock_increment.assert_called_once_with(-200)


def test_none_event_id_is_stored_in_record(mock_db: MagicMock, mock_increment: MagicMock) -> None:
    update_user_bonus_atomic(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=100,
        event_type="admin",
        event_id=None,
    )

    _ref, record = mock_db.batch.return_value.set.call_args.args
    assert "event_id" in record
    assert record["event_id"] is None
