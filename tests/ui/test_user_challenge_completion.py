"""Completing a challenge on the «Мои задания» page reports the outcome to the user.

The message is shown in a dialog (``st.dialog``, formerly ``st.experimental_dialog``). The tests
only assert that the message reaches the rendered page and that the service was called with
the right arguments, so they hold whichever way the dialog is triggered.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any
from unittest.mock import MagicMock

from streamlit.testing.v1 import AppTest

from m8_team.backend.domain.enums import ChallengeStatus
from m8_team.backend.domain.models import UserChallenge
from m8_team.backend.domain.results import ChallengeCompletion

Find = Callable[[Any, str], Any]


def _challenges_app() -> None:
    from m8_team.ui.user.pages.challenges import render_challenges_page

    render_challenges_page()


def _texts(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown]


def _serve(container: MagicMock, ongoing: UserChallenge) -> None:
    container.challenge.assignments.side_effect = lambda _user_id, status: (
        [ongoing] if status == ChallengeStatus.ONGOING else []
    )


def test_page_lists_ongoing_challenge(
    make_app: Callable[..., AppTest],
    container: MagicMock,
    ongoing_challenge: UserChallenge,
    user_session: dict[str, Any],
) -> None:
    _serve(container, ongoing_challenge)
    at = make_app(_challenges_app, session=user_session).run()
    assert not at.exception
    assert "Написать пост" in _texts(at)


def test_completing_on_time_reports_reward(
    make_app: Callable[..., AppTest],
    container: MagicMock,
    ongoing_challenge: UserChallenge,
    user_session: dict[str, Any],
    find: Find,
) -> None:
    _serve(container, ongoing_challenge)
    container.challenge.complete.return_value = ChallengeCompletion("uc1", True, 10)
    at = make_app(_challenges_app, session=user_session).run()

    find(at.button, "Завершить").click().run()

    assert not at.exception
    container.challenge.complete.assert_called_once_with(
        user_challenge_id="uc1", user_id="ivan", planned_finish=date(2025, 1, 5)
    )
    assert "Задание закрыто вовремя. Начислено 10 бонусов" in _texts(at)


def test_completing_late_reports_no_reward(
    make_app: Callable[..., AppTest],
    container: MagicMock,
    ongoing_challenge: UserChallenge,
    user_session: dict[str, Any],
    find: Find,
) -> None:
    _serve(container, ongoing_challenge)
    container.challenge.complete.return_value = ChallengeCompletion("uc1", False, 0)
    at = make_app(_challenges_app, session=user_session).run()

    find(at.button, "Завершить").click().run()

    assert not at.exception
    assert any("закрыто с опозданием" in text for text in _texts(at))
