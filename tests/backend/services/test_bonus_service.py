from unittest.mock import MagicMock

import pytest

from m8_team.backend.domain.enums import TransactionType
from m8_team.backend.domain.errors import InsufficientBalance, PersistenceError
from m8_team.backend.services.bonus_service import BonusService


@pytest.fixture
def ledger() -> MagicMock:
    m = MagicMock()
    m.charge_atomic.return_value = True
    return m


@pytest.fixture
def users() -> MagicMock:
    m = MagicMock()
    m.free_bonuses.return_value = 1000
    return m


@pytest.fixture
def notifications() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(ledger: MagicMock, users: MagicMock, notifications: MagicMock) -> BonusService:
    return BonusService(ledger, users, notifications)


def test_charge_passes_positive_delta_and_notifies(
    service: BonusService, ledger: MagicMock, notifications: MagicMock
) -> None:
    result = service.admin_adjust(user_id="u1", amount=300, transaction_type=TransactionType.CHARGE)
    assert result.delta == 300
    assert ledger.charge_atomic.call_args.kwargs["bonus_value"] == 300
    notifications.notify_user.assert_called_once()


def test_write_off_sufficient_passes_negative_delta(
    service: BonusService, ledger: MagicMock
) -> None:
    result = service.admin_adjust(
        user_id="u1", amount=200, transaction_type=TransactionType.WRITE_OFF
    )
    assert result.delta == -200
    assert ledger.charge_atomic.call_args.kwargs["bonus_value"] == -200


def test_write_off_insufficient_raises_and_skips_ledger(
    service: BonusService, ledger: MagicMock, users: MagicMock
) -> None:
    users.free_bonuses.return_value = 100
    with pytest.raises(InsufficientBalance):
        service.admin_adjust(user_id="u1", amount=200, transaction_type=TransactionType.WRITE_OFF)
    ledger.charge_atomic.assert_not_called()


def test_persistence_failure_raises(service: BonusService, ledger: MagicMock) -> None:
    ledger.charge_atomic.return_value = False
    with pytest.raises(PersistenceError):
        service.admin_adjust(user_id="u1", amount=50, transaction_type=TransactionType.CHARGE)
