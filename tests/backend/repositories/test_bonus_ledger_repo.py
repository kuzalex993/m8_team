"""Ported from the old ``tests/unit/test_firebase.py``: the atomic bonus write is now
``BonusLedgerRepo.charge_atomic``. The Firestore client is a plain ``MagicMock`` passed in
at construction - no ``firebase_admin`` monkeypatching needed because the repository layer
takes an injected client.
"""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_increment(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("m8_team.backend.repositories.bonus_ledger_repo.firestore.Increment")


def _charge(client: MagicMock, **overrides: object) -> bool:
    kwargs = dict(
        user_id="user123",
        transaction_type="charge bonus",
        bonus_value=500,
        event_type="admin",
        event_id=None,
    )
    kwargs.update(overrides)
    return BonusLedgerRepo(client).charge_atomic(**kwargs)  # type: ignore[arg-type]


def test_success_returns_true(mock_client: MagicMock, mock_increment: MagicMock) -> None:
    assert _charge(mock_client) is True


def test_batch_is_committed(mock_client: MagicMock, mock_increment: MagicMock) -> None:
    _charge(mock_client)
    mock_client.batch.return_value.commit.assert_called_once()


def test_bonus_record_fields(mock_client: MagicMock, mock_increment: MagicMock) -> None:
    _charge(mock_client, event_id=42)
    _ref, record = mock_client.batch.return_value.set.call_args.args
    assert record["user_id"] == "user123"
    assert record["bonus_value"] == 500
    assert record["transaction_type"] == "charge bonus"
    assert record["event_type"] == "admin"
    assert record["event_id"] == 42
    assert "date" in record


def test_user_balance_incremented(mock_client: MagicMock, mock_increment: MagicMock) -> None:
    mock_user_ref = MagicMock()

    def _collection_side(name: str) -> MagicMock:
        coll = MagicMock()
        if name == "users":
            coll.document.return_value = mock_user_ref
        return coll

    mock_client.collection.side_effect = _collection_side

    _charge(mock_client)

    mock_increment.assert_called_once_with(500)
    mock_client.batch.return_value.update.assert_called_once_with(
        mock_user_ref, {"user_free_bonuses": mock_increment.return_value}
    )


def test_commit_failure_returns_false(mock_client: MagicMock, mock_increment: MagicMock) -> None:
    mock_client.batch.return_value.commit.side_effect = Exception("Firestore unavailable")
    assert _charge(mock_client) is False


def test_negative_bonus_passes_negative_to_increment(
    mock_client: MagicMock, mock_increment: MagicMock
) -> None:
    assert _charge(mock_client, transaction_type="write off bonus", bonus_value=-200) is True
    mock_increment.assert_called_once_with(-200)


def test_none_event_id_is_stored_in_record(
    mock_client: MagicMock, mock_increment: MagicMock
) -> None:
    _charge(mock_client, bonus_value=100)
    _ref, record = mock_client.batch.return_value.set.call_args.args
    assert record["event_id"] is None
