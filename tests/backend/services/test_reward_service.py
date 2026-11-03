from unittest.mock import MagicMock

import pytest

from m8_team.backend.domain.errors import PersistenceError, RewardAlreadyResolved
from m8_team.backend.domain.results import RewardResolution
from m8_team.backend.services.reward_service import RewardService


def test_cancel_delegates_by_request_id_without_notifications() -> None:
    ledger, notifications = MagicMock(), MagicMock()
    service = RewardService(MagicMock(), MagicMock(), MagicMock(), ledger, notifications)
    service.cancel(user_reward_id="order")
    ledger.cancel_reserved_atomic.assert_called_once_with(user_reward_id="order")
    assert not notifications.mock_calls


def test_confirmation_notifies_owner_from_committed_decision() -> None:
    ledger, notifications, catalogue = MagicMock(), MagicMock(), MagicMock()
    ledger.settle_reserved_atomic.return_value = RewardResolution("owner", "Кофе", 100)
    service = RewardService(catalogue, MagicMock(), MagicMock(), ledger, notifications)
    service.confirm(user_reward_id="order")
    ledger.settle_reserved_atomic.assert_called_once_with(user_reward_id="order")
    notifications.notify_user.assert_called_once_with(
        "owner", "Ура! Админ подтвердил награду: Кофе"
    )
    assert not catalogue.mock_calls


@pytest.mark.parametrize("error", [PersistenceError, RewardAlreadyResolved])
def test_failed_confirmation_does_not_notify(error: type[Exception]) -> None:
    ledger, notifications = MagicMock(), MagicMock()
    ledger.settle_reserved_atomic.side_effect = error
    service = RewardService(MagicMock(), MagicMock(), MagicMock(), ledger, notifications)
    with pytest.raises(error):
        service.confirm(user_reward_id="order")
    assert not notifications.mock_calls
