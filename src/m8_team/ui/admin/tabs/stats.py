"""'Статистика' tab (was ``components/admin/stats_tab.py``). Aggregation lives in
``stats`` service; this module only picks the date range and draws charts.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from m8_team.ui.common import cache
from m8_team.ui.container import get_container

EARLIEST_DATE = date(2024, 1, 1)


def default_bonus_range(today: date) -> tuple[date, date]:
    """Default period: three calendar months back from ``today`` up to ``today``."""
    three_months_ago = (pd.Timestamp(today) - pd.DateOffset(months=3)).date()
    return max(three_months_ago, EARLIEST_DATE), today


def _render_bonus_range_picker() -> tuple[date, date] | None:
    latest_date = date.today()
    selected_range = st.date_input(
        label="Период",
        value=default_bonus_range(latest_date),
        min_value=EARLIEST_DATE,
        max_value=latest_date,
        format="DD.MM.YYYY",
        key="bonus_stats_date_range",
    )
    if not isinstance(selected_range, tuple) or len(selected_range) != 2:
        st.info("Выберите начальную и конечную дату периода.")
        return None
    start_date, end_date = selected_range
    if start_date > end_date:
        st.warning("Начальная дата не может быть позже конечной.")
        return None
    return start_date, end_date


def _render_bonuses_section(*, include_inactive: bool) -> None:
    stats = get_container().stats
    st.markdown("#### Заработанные бонусы по сотрудникам")
    selected_range = _render_bonus_range_picker()
    if selected_range is None:
        return
    start_date, end_date = selected_range
    bonus_totals = stats.bonuses_earned_by_user(
        cache.earned_bonus_rows(start_date, end_date), include_inactive=include_inactive
    )
    if bonus_totals.empty:
        st.info("За выбранный период никто не заработал бонусов.")
    else:
        st.bar_chart(bonus_totals)


def _render_finished_challenges_section(*, include_inactive: bool) -> None:
    stats = get_container().stats
    st.markdown("#### Выполненные задания по сотрудникам")
    finished_challenges_df = stats.finished_challenges_by_user(
        cache.user_challenge_df(), include_inactive=include_inactive
    )
    if finished_challenges_df.empty:
        st.info("Пока никто не завершил ни одного задания.")
    else:
        st.bar_chart(finished_challenges_df, color=["#2ecc71", "#e74c3c"])


def render_stats_tab() -> None:
    st.subheader("Статистика")
    include_inactive = st.toggle(
        "Показать бывших сотрудников",
        key="stats_include_former",
        help=(
            "По умолчанию в статистике только сотрудники, которые работают в команде. "
            "Бывшие — отключённые в карточке сотрудника и те, чей профиль удалён."
        ),
    )

    _render_bonuses_section(include_inactive=include_inactive)
    st.divider()
    _render_finished_challenges_section(include_inactive=include_inactive)
