"""The edit forms in the Задания / Награды tabs must show the selected item's current values.

Since Streamlit ~1.4x a widget with a ``key`` keeps its identity when ``value=`` changes, so
choosing another item in the selectbox no longer resets the text/number inputs. The forms then
stay empty and submitting them would blank the item in Firestore.

Widgets are located by label, not key, so the tests do not depend on how the fix wires keys.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

Find = Callable[[Any, str], Any]


def _tasks_app() -> None:
    from m8_team.ui.admin.tabs.tasks import render_tasks_tab

    render_tasks_tab()


def _rewards_app() -> None:
    from m8_team.ui.admin.tabs.rewards import render_rewards_tab

    render_rewards_tab()


def test_task_edit_form_shows_selected_task(make_app: Callable[..., AppTest], find: Find) -> None:
    at = make_app(_tasks_app).run()
    assert not at.exception

    at.selectbox(key="challenge_to_edit").select("Написать пост").run()
    assert find(at.text_area, "Новое задание").value == "Написать пост"
    assert find(at.number_input, "Новая награда за выполнение").value == 10
    assert find(at.number_input, "Новое время на выполнение").value == 3

    # Switching to another task must replace the values, not keep the previous ones.
    at.selectbox(key="challenge_to_edit").select("Снять ролик").run()
    assert find(at.text_area, "Новое задание").value == "Снять ролик"
    assert find(at.number_input, "Новая награда за выполнение").value == 25
    assert find(at.number_input, "Новое время на выполнение").value == 7


def test_task_edit_submit_sends_selected_values(
    make_app: Callable[..., AppTest], container: MagicMock, find: Find
) -> None:
    container.challenge.update_catalogue_item.return_value = True
    at = make_app(_tasks_app).run()
    at.selectbox(key="challenge_to_edit").select("Снять ролик").run()

    find(at.button, "Применить изменения").click().run()

    container.challenge.update_catalogue_item.assert_called_once_with(
        "c2", description="Снять ролик", reward=25, planned_time=7
    )


def test_reward_edit_form_shows_selected_reward(
    make_app: Callable[..., AppTest], find: Find
) -> None:
    at = make_app(_rewards_app).run()
    assert not at.exception

    at.selectbox(key="reward_to_edit").select("Выходной день").run()
    assert find(at.text_area, "Новая награда").value == "Выходной день"
    assert find(at.number_input, "Новая стоимость награды").value == 100

    at.selectbox(key="reward_to_edit").select("Кофе").run()
    assert find(at.text_area, "Новая награда").value == "Кофе"
    assert find(at.number_input, "Новая стоимость награды").value == 15


def test_reward_edit_submit_sends_selected_values(
    make_app: Callable[..., AppTest], container: MagicMock, find: Find
) -> None:
    container.reward.update_catalogue_item.return_value = True
    at = make_app(_rewards_app).run()
    at.selectbox(key="reward_to_edit").select("Кофе").run()

    find(at.button, "Применить изменения").click().run()

    container.reward.update_catalogue_item.assert_called_once_with(
        "r2", description="Кофе", price=15
    )


@pytest.mark.parametrize(
    ("app", "select_key", "label"),
    [
        (_tasks_app, "challenge_to_edit", "Новое задание"),
        (_rewards_app, "reward_to_edit", "Новая награда"),
    ],
)
def test_edit_form_is_empty_until_an_item_is_selected(
    make_app: Callable[..., AppTest],
    app: Callable[[], None],
    select_key: str,
    label: str,
    find: Find,
) -> None:
    at = make_app(app).run()
    assert at.selectbox(key=select_key).value is None
    assert find(at.text_area, label).value == ""
