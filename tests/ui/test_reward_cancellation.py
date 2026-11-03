from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

from m8_team.backend.domain.errors import PersistenceError, RewardAlreadyResolved


def _requests() -> None:
    from m8_team.ui.admin.tabs.requests import render_requests_tab

    render_requests_tab()


def _bonuses() -> None:
    from m8_team.ui.user.pages.bonuses import render_bonuses_page

    render_bonuses_page()


def test_cancel_removes_card_and_preserves_history(
    make_app: Callable[..., AppTest],
    container: MagicMock,
) -> None:
    order = container.reward.requests.return_value[0]

    def cancel(**kwargs: Any) -> None:
        assert kwargs == {"user_reward_id": "ur1"}
        order.user_reward_status = "cancelled"
        order.user_reward_decision_date = "2026-11-03T10:00:00Z"

    container.reward.cancel.side_effect = cancel
    at = make_app(
        _requests,
        session={
            "user_id": "admin",
            "selected_user_name": "Иван",
            "users_data_map": {"Иван": "ivan"},
            "current_user_balance": 0,
        },
    ).run()
    next(b for b in at.button if b.label == "Отменить").click().run()
    assert not at.exception
    assert not at.button
    assert any("Баллы возвращены" in x.value for x in at.success)
    assert "Отменена" in at.dataframe[0].value["status"].tolist()
    assert at.session_state["current_user_balance"] == 120
    container.reward.confirm.assert_not_called()


@pytest.mark.parametrize(
    "error,message",
    [
        (PersistenceError, "Не удалось"),
        (RewardAlreadyResolved, "уже обработана"),
    ],
)
def test_failed_cancel_reports_result(
    make_app: Callable[..., AppTest],
    container: MagicMock,
    error: type[Exception],
    message: str,
) -> None:
    def cancel(**kwargs: Any) -> None:
        if error is RewardAlreadyResolved:
            container.reward.requests.return_value[0].user_reward_status = "completed"
        raise error

    container.reward.cancel.side_effect = cancel
    at = make_app(_requests, session={"user_id": "admin"}).run()
    next(b for b in at.button if b.label == "Отменить").click().run()
    assert not at.exception
    assert any(message in x.value for x in at.error)
    assert bool(at.button) is (error is PersistenceError)


def test_regular_user_cannot_invoke_admin_callback(
    make_app: Callable[..., AppTest],
    container: MagicMock,
) -> None:
    at = make_app(_requests, session={"user_id": "ivan"}).run()
    next(b for b in at.button if b.label == "Отменить").click().run()
    container.reward.cancel.assert_not_called()
    assert any("Недостаточно прав" in x.value for x in at.error)


def test_user_history_shows_cancelled_without_admin_actions(
    make_app: Callable[..., AppTest],
    container: MagicMock,
    user_session: dict[str, Any],
) -> None:
    container.reward.requests.return_value[0].user_reward_status = "cancelled"
    at = make_app(_bonuses, session=user_session).run()
    assert not at.exception
    assert "Отменена" in at.dataframe[0].value["status"].tolist()
    assert not any(b.label in {"Отменить", "Подтвердить"} for b in at.button)
