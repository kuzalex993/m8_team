"""'Статистика' tab (was ``components/admin/stats_tab.py``). Aggregation lives in
``stats`` service; this module only picks the date range and draws charts.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from m8_team.ui.common import cache
from m8_team.ui.container import get_container


def _render_bonus_range_picker() -> tuple[date, date] | None:
    earliest_date = date(2024, 1, 1)
    latest_date = date.today()
    default_start = max(latest_date - timedelta(days=30), earliest_date)
    selected_range = st.date_input(
        label="Период",
        value=(default_start, latest_date),
        min_value=earliest_date,
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


def render_stats_tab() -> None:
    stats = get_container().stats
    st.subheader("Статистика")

    st.markdown("#### Выполненные задания по сотрудникам")
    finished_challenges_df = stats.finished_challenges_by_user(cache.user_challenge_df())
    if finished_challenges_df.empty:
        st.info("Пока никто не завершил ни одного задания.")
    else:
        st.bar_chart(finished_challenges_df, color=["#2ecc71", "#e74c3c"])

    st.divider()
    st.markdown("#### Заработанные бонусы по сотрудникам")
    selected_range = _render_bonus_range_picker()
    if selected_range is not None:
        start_date, end_date = selected_range
        bonus_totals = stats.bonuses_earned_by_user(cache.earned_bonus_rows(start_date, end_date))
        if bonus_totals.empty:
            st.info("За выбранный период никто не заработал бонусов.")
        else:
            st.bar_chart(bonus_totals)
