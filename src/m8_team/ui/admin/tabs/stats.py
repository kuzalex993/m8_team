"""'Статистика' tab (was ``components/admin/stats_tab.py``). Aggregation lives in
``stats`` service; this module only picks the date range and draws charts.
"""

from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from m8_team.backend.services.stats_service import FAILURE_COLUMN, SUCCESS_COLUMN
from m8_team.ui.common import cache
from m8_team.ui.container import get_container

EARLIEST_DATE = date(2024, 1, 1)

# Each chart has its own period picker, so they are independent.
BONUSES_PERIOD_KEY = "bonus_stats_date_range"
CHALLENGES_PERIOD_KEY = "challenges_stats_date_range"

# Chart field names: Vega shows them in the tooltip and as the legend title.
NAME_LABEL = "Имя"
BONUSES_LABEL = "Бонусов"
SOURCE_LABEL = "Тип"
CHALLENGES_LABEL = "Заданий"
RESULT_LABEL = "Результат"
SUCCESS_COLOR = "#2ecc71"
FAILURE_COLOR = "#e74c3c"


def default_period(today: date) -> tuple[date, date]:
    """Default period: three calendar months back from ``today`` up to ``today``."""
    three_months_ago = (pd.Timestamp(today) - pd.DateOffset(months=3)).date()
    return max(three_months_ago, EARLIEST_DATE), today


def _render_period_picker(key: str) -> tuple[date, date] | None:
    latest_date = date.today()
    selected_range = st.date_input(
        label="Период",
        value=default_period(latest_date),
        min_value=EARLIEST_DATE,
        max_value=latest_date,
        format="DD.MM.YYYY",
        key=key,
    )
    if not isinstance(selected_range, tuple) or len(selected_range) != 2:
        st.info("Выберите начальную и конечную дату периода.")
        return None
    start_date, end_date = selected_range
    if start_date > end_date:
        st.warning("Начальная дата не может быть позже конечной.")
        return None
    return start_date, end_date


def bonuses_long_format(bonus_totals: pd.DataFrame) -> pd.DataFrame:
    """Wide ``user_name x source`` table -> long ``Имя / Тип / Бонусов`` rows, the shape
    ``st.bar_chart`` needs to stack by ``Тип`` under Russian field names."""
    return (
        bonus_totals.rename_axis(NAME_LABEL)
        .reset_index()
        .melt(id_vars=NAME_LABEL, var_name=SOURCE_LABEL, value_name=BONUSES_LABEL)
    )


def finished_challenges_long_format(counts: pd.DataFrame) -> pd.DataFrame:
    """Wide ``user_name x (Успешно, Неуспешно)`` table -> long ``Имя / Результат / Заданий``
    rows for the stacked chart."""
    return (
        counts.rename_axis(NAME_LABEL)
        .reset_index()
        .melt(id_vars=NAME_LABEL, var_name=RESULT_LABEL, value_name=CHALLENGES_LABEL)
    )


def finished_challenges_chart(counts: pd.DataFrame) -> alt.Chart:
    """Stacked bars per employee, green for successful and red for unsuccessful. Drawn with
    Altair (not ``st.bar_chart``) to keep those colours *and* Russian names in the tooltip
    and legend; axis titles are hidden."""
    chart: alt.Chart = (
        alt.Chart(finished_challenges_long_format(counts))
        .mark_bar()
        .encode(
            x=alt.X(f"{NAME_LABEL}:N", title=None),
            y=alt.Y(f"{CHALLENGES_LABEL}:Q", title=None),
            color=alt.Color(
                f"{RESULT_LABEL}:N",
                scale=alt.Scale(
                    domain=[SUCCESS_COLUMN, FAILURE_COLUMN], range=[SUCCESS_COLOR, FAILURE_COLOR]
                ),
            ),
            tooltip=[NAME_LABEL, CHALLENGES_LABEL, RESULT_LABEL],
        )
    )
    return chart


def _render_bonuses_section(*, include_inactive: bool) -> None:
    stats = get_container().stats
    st.markdown("#### Заработанные бонусы по сотрудникам")
    selected_range = _render_period_picker(BONUSES_PERIOD_KEY)
    if selected_range is None:
        return
    start_date, end_date = selected_range
    bonus_totals = stats.bonuses_earned_by_user(
        cache.earned_bonus_rows(start_date, end_date), include_inactive=include_inactive
    )
    if bonus_totals.empty:
        st.info("За выбранный период никто не заработал бонусов.")
    else:
        st.bar_chart(
            bonuses_long_format(bonus_totals),
            x=NAME_LABEL,
            y=BONUSES_LABEL,
            color=SOURCE_LABEL,
            x_label="",  # the field names are for the tooltip and legend, not axis titles
            y_label="",
        )


def _render_finished_challenges_section(*, include_inactive: bool) -> None:
    stats = get_container().stats
    st.markdown("#### Выполненные задания по сотрудникам")
    period = _render_period_picker(CHALLENGES_PERIOD_KEY)
    if period is None:
        return
    finished_counts = stats.finished_challenges_by_user(
        cache.user_challenge_df(), period=period, include_inactive=include_inactive
    )
    if finished_counts.empty:
        st.info("За выбранный период никто не завершил ни одного задания.")
    else:
        st.altair_chart(finished_challenges_chart(finished_counts), width="stretch")


def render_stats_tab() -> None:
    st.subheader("Статистика")
    include_inactive = st.toggle(
        "Добавить бывших сотрудников",
        key="stats_include_former",
        help=(
            "По умолчанию в статистике только сотрудники,"
            "которые работают в команде на текущий момент.\n"
            "Бывшие сотруник - это тот, в чьей карточке переключатель "
            "'Работает в команде' выключен."
            "А также тот, чей профиль был ранее удалён."
        ),
    )

    _render_bonuses_section(include_inactive=include_inactive)
    st.divider()
    _render_finished_challenges_section(include_inactive=include_inactive)
