"""Opt-in Firestore checks, restricted to emulator or an explicitly selected dev project."""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.transaction import Transaction
from google.oauth2 import service_account
from pytest_mock import MockerFixture

from m8_team.backend.domain.errors import PersistenceError, RewardAlreadyResolved
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo


@pytest.fixture
def database() -> Iterator[tuple[Any, str, list[str]]]:
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        client = firestore.Client(
            project="demo-reward-resolution",
            credentials=AnonymousCredentials(),  # type: ignore[no-untyped-call]
        )
    elif os.getenv("REWARD_TEST_PROJECT") and os.getenv("REWARD_TEST_CREDENTIALS"):
        project = os.environ["REWARD_TEST_PROJECT"]
        credentials = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
            os.environ["REWARD_TEST_CREDENTIALS"]
        )
        if credentials.project_id != project or "dev" not in project:
            pytest.fail("Live checks require an explicitly selected matching dev project")
        client = firestore.Client(project=project, credentials=credentials)
    else:
        pytest.skip("Set FIRESTORE_EMULATOR_HOST or explicit dev project and test credentials")
    prefix = "reward-cancel-test-" + uuid4().hex
    user_id = prefix + "-user"
    orders = [prefix + "-order-1", prefix + "-order-2"]
    batch = client.batch()
    batch.create(
        client.collection("users").document(user_id),
        {
            "user_free_bonuses": 20,
            "user_reserved_bonuses": 200,
        },
    )
    for order_id in orders:
        batch.create(
            client.collection("user_reward").document(order_id),
            {
                "user_id": user_id,
                "user_reward_status": "new",
                "reward_description": "Test reward",
            },
        )
        batch.create(
            client.collection("user_bonus").document(order_id + "-reservation"),
            {
                "user_id": user_id,
                "event_id": order_id,
                "event_type": "user_reward",
                "transaction_type": "reserve bonus",
                "bonus_value": 100,
            },
        )
    batch.commit(timeout=20)
    try:
        yield client, user_id, orders
    finally:
        # Only remove this fixture's uniquely named synthetic documents and linked ledger rows.
        cleanup = client.batch()
        cleanup.delete(client.collection("users").document(user_id))
        for order_id in orders:
            cleanup.delete(client.collection("user_reward").document(order_id))
            for doc in (
                client.collection("user_bonus")
                .where(filter=FieldFilter("event_id", "==", order_id))
                .stream(timeout=20)
            ):
                cleanup.delete(doc.reference)
        cleanup.commit(timeout=20)
        client.close()  # type: ignore[no-untyped-call]


def _assert_state(
    database: tuple[Any, str, list[str]], expected_free: int, expected_reserved: int
) -> list[dict[str, Any]]:
    client, user_id, orders = database
    user = client.collection("users").document(user_id).get(timeout=20).to_dict()
    assert user["user_free_bonuses"] == expected_free
    assert user["user_reserved_bonuses"] == expected_reserved
    decisions = []
    for order_id in orders:
        records = [
            doc.to_dict()
            for doc in client.collection("user_bonus")
            .where(filter=FieldFilter("event_id", "==", order_id))
            .stream(timeout=20)
        ]
        reservation = [r for r in records if r["transaction_type"] == "reserve bonus"]
        assert len(reservation) == 1
        for record in records:
            assert record["user_id"] == user_id
            assert record["bonus_value"] == 100
            assert record["event_type"] == "user_reward"
        terminal = [r for r in records if r["transaction_type"] != "reserve bonus"]
        assert len(terminal) <= 1
        order = client.collection("user_reward").document(order_id).get(timeout=20).to_dict()
        if terminal:
            expected = (
                "cancelled" if terminal[0]["transaction_type"] == "refund bonus" else "completed"
            )
            assert order["user_reward_status"] == expected
            assert order["user_reward_decision_date"] == terminal[0]["date"]
        else:
            assert order["user_reward_status"] == "new"
        decisions.extend(terminal)
    return decisions


def test_cancel_then_retry(database: tuple[Any, str, list[str]]) -> None:
    client, _, orders = database
    repo = BonusLedgerRepo(client)
    repo.cancel_reserved_atomic(user_reward_id=orders[0])
    with pytest.raises(RewardAlreadyResolved):
        repo.cancel_reserved_atomic(user_reward_id=orders[0])
    assert len(_assert_state(database, 120, 100)) == 1


@pytest.mark.parametrize("actions", ["same-order", "confirm-cancel", "two-orders"])
def test_concurrent_decisions(database: tuple[Any, str, list[str]], actions: str) -> None:
    client, _, orders = database
    gate = Barrier(2)

    def decide(index: int) -> bool:
        repo = BonusLedgerRepo(client)
        gate.wait(timeout=10)
        try:
            if actions == "confirm-cancel" and index == 0:
                repo.settle_reserved_atomic(user_reward_id=orders[0])
            else:
                order_id = orders[index] if actions == "two-orders" else orders[0]
                repo.cancel_reserved_atomic(user_reward_id=order_id)
            return True
        except RewardAlreadyResolved:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(decide, [0, 1]))
    assert sum(results) == (2 if actions == "two-orders" else 1)
    if actions == "two-orders":
        assert len(_assert_state(database, 220, 0)) == 2
    else:
        status = (
            client.collection("user_reward")
            .document(orders[0])
            .get()
            .to_dict()["user_reward_status"]
        )
        assert len(_assert_state(database, 120 if status == "cancelled" else 20, 100)) == 1


def test_commit_failure_leaves_all_documents_unchanged(
    database: tuple[Any, str, list[str]],
    mocker: MockerFixture,
) -> None:
    client, _, orders = database
    mocker.patch.object(Transaction, "_commit", side_effect=RuntimeError("injected commit failure"))
    with pytest.raises(PersistenceError):
        BonusLedgerRepo(client).cancel_reserved_atomic(user_reward_id=orders[0])
    assert not _assert_state(database, 20, 200)
