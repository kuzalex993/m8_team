"""Characterization tests: every page/tab renders on the installed Streamlit without raising.

These guard the parts of the UI that already work on 1.62 (dataframes with ``column_config``,
charts, date pickers, metrics, forms) against regressions while the deprecated calls are migrated.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

Find = Callable[[Any, str], Any]


def _employees() -> None:
    from m8_team.ui.admin.tabs.employees import render_employees_tab

    render_employees_tab()


def _requests() -> None:
    from m8_team.ui.admin.tabs.requests import render_requests_tab

    render_requests_tab()


def _stats() -> None:
    from m8_team.ui.admin.tabs.stats import render_stats_tab

    render_stats_tab()


def _tasks() -> None:
    from m8_team.ui.admin.tabs.tasks import render_tasks_tab

    render_tasks_tab()


def _rewards() -> None:
    from m8_team.ui.admin.tabs.rewards import render_rewards_tab

    render_rewards_tab()


def _bonuses() -> None:
    from m8_team.ui.user.pages.bonuses import render_bonuses_page

    render_bonuses_page()


def _settings() -> None:
    from m8_team.ui.user.pages.settings import render_settings_page

    render_settings_page()


ADMIN_STATE = {
    # Primed by ``ensure_session_state`` in the real admin page.
    "current_user_balance": None,
    "insufficient_balance_error": False,
    "additional_bonus_widget": 0,
}


@pytest.mark.parametrize(
    ("app", "as_user"),
    [
        (_employees, False),
        (_requests, False),
        (_stats, False),
        (_tasks, False),
        (_rewards, False),
        (_bonuses, True),
        (_settings, True),
    ],
    ids=lambda v: v.__name__.strip("_") if callable(v) else "",
)
def test_page_renders(
    make_app: Callable[..., AppTest],
    user_session: dict[str, Any],
    app: Callable[[], None],
    as_user: bool,
) -> None:
    session = user_session if as_user else ADMIN_STATE
    at = make_app(app, session=session).run()
    assert not at.exception


def test_employee_tabs_render_after_selecting_a_user(
    make_app: Callable[..., AppTest], find: Find
) -> None:
    at = make_app(_employees, session=ADMIN_STATE).run()

    at.selectbox(key="selected_user_name").select("Иван").run()

    assert not at.exception
    assert len(at.tabs) == 2
    assert find(at.button, "Изменить баланс")
    assert find(at.button, "Назначить задание")
    assert len(at.dataframe) == 1  # the user's open assignments


def test_employee_toggle_calls_set_active(make_app: Callable[..., AppTest], container: Any) -> None:
    container.user.set_active.return_value = True
    at = make_app(_employees, session=ADMIN_STATE).run()
    at.selectbox(key="selected_user_name").select("Иван").run()

    toggle = at.toggle(key="is_active_ivan")
    assert toggle.value is True  # docs without the field count as active
    toggle.set_value(False).run()

    container.user.set_active.assert_called_once_with("ivan", False)
    assert not at.exception
    assert any("обновлен" in m.value for m in at.success)


def test_former_employees_hidden_until_toggle_on(
    make_app: Callable[..., AppTest], container: Any
) -> None:
    container.user.employee_directory.return_value = [
        ("Иван", "ivan", True),
        ("Пётр", "petr", False),
    ]
    at = make_app(_employees, session=ADMIN_STATE).run()
    assert at.selectbox(key="selected_user_name").options == ["Иван"]

    at.toggle(key="show_former_employees").set_value(True).run()
    assert at.selectbox(key="selected_user_name").options == ["Иван", "Пётр"]


def test_admin_requests_lists_pending_request(make_app: Callable[..., AppTest], find: Find) -> None:
    at = make_app(_requests).run()
    assert not at.exception
    assert find(at.button, "Подтвердить")
    assert len(at.dataframe) == 1  # decided requests


def test_stats_renders_both_charts(make_app: Callable[..., AppTest]) -> None:
    at = make_app(_stats).run()
    assert not at.exception
    assert len(at.get("vega_lite_chart")) == 2


def test_stats_bonus_chart_uses_russian_field_names(make_app: Callable[..., AppTest]) -> None:
    at = make_app(_stats).run()

    assert not at.exception
    spec = json.loads(at.get("vega_lite_chart")[0].proto.spec)
    encoding = spec["encoding"]
    assert [encoding[c]["field"] for c in ("x", "y", "color")] == ["Имя", "Бонусов", "Тип"]
    assert [t["field"] for t in encoding["tooltip"]] == ["Имя", "Бонусов", "Тип"]
    assert encoding["x"]["title"] is None and encoding["y"]["title"] is None  # no axis titles
    assert "scale" not in encoding["color"]  # default palette; ``scale: null`` would break it


def test_stats_challenges_chart_is_stacked_green_and_red_with_russian_names(
    make_app: Callable[..., AppTest],
) -> None:
    at = make_app(_stats).run()

    assert not at.exception
    encoding = json.loads(at.get("vega_lite_chart")[1].proto.spec)["encoding"]
    assert [encoding[c]["field"] for c in ("x", "y", "color")] == ["Имя", "Заданий", "Результат"]
    assert [t["field"] for t in encoding["tooltip"]] == ["Имя", "Заданий", "Результат"]
    assert encoding["x"]["title"] is None and encoding["y"]["title"] is None  # no axis titles
    scale = encoding["color"]["scale"]
    assert dict(zip(scale["domain"], scale["range"], strict=True)) == {
        "Успешно": "#2ecc71",
        "Неуспешно": "#e74c3c",
    }


def test_stats_charts_have_their_legend_on_the_right(make_app: Callable[..., AppTest]) -> None:
    at = make_app(_stats).run()

    assert not at.exception
    charts = at.get("vega_lite_chart")
    assert len(charts) == 2
    for chart in charts:
        encoding = json.loads(chart.proto.spec)["encoding"]
        assert encoding["color"]["legend"]["orient"] == "right"


def test_stats_period_defaults_to_last_three_months(make_app: Callable[..., AppTest]) -> None:
    from m8_team.ui.admin.tabs.stats import default_period

    at = make_app(_stats).run()

    expected = default_period(date.today())
    assert at.date_input(key="bonus_stats_date_range").value == expected
    assert at.date_input(key="challenges_stats_date_range").value == expected


def test_stats_challenges_chart_is_filtered_by_its_own_period(
    make_app: Callable[..., AppTest], container: Any
) -> None:
    at = make_app(_stats).run()
    container.stats.finished_challenges_by_user.reset_mock()

    new_period = (date(2026, 1, 1), date(2026, 1, 31))
    at.date_input(key="challenges_stats_date_range").set_value(new_period).run()

    assert not at.exception
    assert container.stats.finished_challenges_by_user.call_args.kwargs["period"] == new_period
    # the bonuses picker is independent
    assert at.date_input(key="bonus_stats_date_range").value != new_period


def test_user_bonuses_page_shows_balance(
    make_app: Callable[..., AppTest], user_session: dict[str, Any]
) -> None:
    at = make_app(_bonuses, session=user_session).run()
    assert not at.exception
    texts = [m.value for m in at.markdown]
    assert "**Доступные бонусы:** 120" in texts
    assert "**Бонусы в резерве:** 10" in texts
