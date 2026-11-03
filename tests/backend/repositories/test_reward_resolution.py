"""Decision validation and writes, without credentials or a live Firestore server."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from m8_team.backend.domain.errors import (
    InsufficientReservedBonuses,
    InvalidReservation,
    NotFound,
    PersistenceError,
    RewardAlreadyResolved,
)
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo


@pytest.fixture
def decision(mocker: MockerFixture) -> tuple[BonusLedgerRepo, MagicMock, MagicMock]:
    client = MagicMock()
    transaction = client.transaction.return_value
    mocker.patch(
        "m8_team.backend.repositories.bonus_ledger_repo.transactional",
        side_effect=lambda callback: callback,
    )
    client.collection.return_value.document.return_value.get.return_value.to_dict.side_effect = [
        {"user_reward_status": "new", "user_id": "owner", "reward_description": "Кофе"},
        {"user_reserved_bonuses": 100, "user_free_bonuses": 20},
    ]
    snapshot = MagicMock()
    snapshot.id = "reservation-id-different-from-request"
    snapshot.to_dict.return_value = {
        "transaction_type": "reserve bonus",
        "event_type": "user_reward",
        "event_id": "request",
        "user_id": "owner",
        "bonus_value": 100,
    }
    transaction.get.return_value = [snapshot]
    return BonusLedgerRepo(client), client, transaction


def test_cancel_returns_reservation_and_commits_all_writes(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock],
) -> None:
    repo, client, transaction = decision
    result = repo.cancel_reserved_atomic(user_reward_id="request")
    assert result.amount == 100
    assert result.user_id == "owner"
    writes = [call.args[1] for call in transaction.update.call_args_list]
    assert writes[0] == {"user_free_bonuses": 120, "user_reserved_bonuses": 0}
    assert writes[1]["user_reward_status"] == "cancelled"
    record = transaction.create.call_args.args[1]
    assert record == {
        "transaction_type": "refund bonus",
        "event_type": "user_reward",
        "event_id": "request",
        "user_id": "owner",
        "bonus_value": 100,
        "date": writes[1]["user_reward_decision_date"],
    }
    client.batch.assert_not_called()


def test_confirmation_uses_reservation_without_catalogue(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock],
) -> None:
    repo, client, transaction = decision
    assert repo.settle_reserved_atomic(user_reward_id="request").amount == 100
    writes = [call.args[1] for call in transaction.update.call_args_list]
    assert writes[0] == {"user_reserved_bonuses": 0}
    assert writes[1]["user_reward_status"] == "completed"
    assert transaction.create.call_args.args[1]["transaction_type"] == "debiting bonus"
    assert all(call.args[0] != "rewards" for call in client.collection.call_args_list)


@pytest.mark.parametrize("cancel", [True, False])
@pytest.mark.parametrize("status", ["completed", "cancelled"])
def test_resolved_order_has_no_writes(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock], cancel: bool, status: str
) -> None:
    repo, client, transaction = decision
    client.collection.return_value.document.return_value.get.return_value.to_dict.side_effect = [
        {"user_reward_status": status},
    ]
    with pytest.raises(RewardAlreadyResolved):
        repo._resolve_reserved_atomic(user_reward_id="request", cancel=cancel)
    transaction.update.assert_not_called()
    transaction.create.assert_not_called()


@pytest.mark.parametrize("records", [[], [MagicMock(), MagicMock()]])
def test_missing_or_ambiguous_reservation(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock], records: list[MagicMock]
) -> None:
    repo, _, transaction = decision
    for record in records:
        record.to_dict.return_value = {"transaction_type": "reserve bonus"}
    transaction.get.return_value = records
    with pytest.raises(InvalidReservation):
        repo.cancel_reserved_atomic(user_reward_id="request")
    transaction.update.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("user_id", "someone-else"),
        ("event_type", "admin"),
        ("bonus_value", 0),
        ("bonus_value", -10),
        ("bonus_value", True),
        ("bonus_value", "100"),
        ("bonus_value", 1.5),
    ],
)
def test_invalid_reservation_has_no_writes(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock], field: str, value: object
) -> None:
    repo, _, transaction = decision
    transaction.get.return_value[0].to_dict.return_value[field] = value
    with pytest.raises(InvalidReservation):
        repo.cancel_reserved_atomic(user_reward_id="request")
    transaction.update.assert_not_called()


def test_insufficient_reserve_has_no_writes(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock],
) -> None:
    repo, client, transaction = decision
    client.collection.return_value.document.return_value.get.return_value.to_dict.side_effect = [
        {"user_reward_status": "new", "user_id": "owner"},
        {"user_reserved_bonuses": 99, "user_free_bonuses": 20},
    ]
    with pytest.raises(InsufficientReservedBonuses):
        repo.cancel_reserved_atomic(user_reward_id="request")
    transaction.update.assert_not_called()


@pytest.mark.parametrize(
    "documents",
    [
        [None],
        [
            {"user_reward_status": "new", "user_id": "owner"},
            None,
        ],
    ],
)
def test_missing_documents(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock], documents: list[dict[str, Any] | None]
) -> None:
    repo, client, transaction = decision
    client.collection.return_value.document.return_value.get.return_value.to_dict.side_effect = (
        documents
    )
    with pytest.raises(NotFound):
        repo.cancel_reserved_atomic(user_reward_id="request")
    transaction.update.assert_not_called()


def test_commit_failure_is_persistence_error(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock], mocker: MockerFixture
) -> None:
    repo, _, _ = decision
    mocker.patch(
        "m8_team.backend.repositories.bonus_ledger_repo.transactional",
        return_value=MagicMock(side_effect=RuntimeError("commit failed")),
    )
    with pytest.raises(PersistenceError):
        repo.cancel_reserved_atomic(user_reward_id="request")


def test_aborted_transaction_retries_after_releasing_locks(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock],
    mocker: MockerFixture,
) -> None:
    from google.api_core.exceptions import Aborted

    from m8_team.backend.domain.results import RewardResolution

    repo, client, _ = decision
    conflict = ValueError("Failed to commit transaction in 1 attempts.")
    conflict.__cause__ = Aborted("transaction conflict")  # type: ignore[no-untyped-call]
    run = MagicMock(side_effect=[conflict, RewardResolution("owner", "Кофе", 100)])
    mocker.patch("m8_team.backend.repositories.bonus_ledger_repo.transactional", return_value=run)
    sleep = mocker.patch("m8_team.backend.repositories.bonus_ledger_repo.time.sleep")
    assert repo.cancel_reserved_atomic(user_reward_id="request").amount == 100
    assert client.transaction.call_count == 2
    sleep.assert_called_once()


def test_unrelated_value_error_is_not_retried(
    decision: tuple[BonusLedgerRepo, MagicMock, MagicMock],
    mocker: MockerFixture,
) -> None:
    repo, client, _ = decision
    run = MagicMock(side_effect=ValueError("invalid data"))
    mocker.patch("m8_team.backend.repositories.bonus_ledger_repo.transactional", return_value=run)
    with pytest.raises(PersistenceError):
        repo.cancel_reserved_atomic(user_reward_id="request")
    assert client.transaction.call_count == 1
