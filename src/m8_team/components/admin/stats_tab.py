"""'Статистика' tab: aggregate views over data the other tabs only show per-employee or
per-record - finished challenges per employee, and bonuses earned per employee over a
selectable date range."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from . import data
from .constants import EXCLUDED_FROM_EMPLOYEE_LIST

_SUCCESS_COLUMN = "Успешно"
_FAILURE_COLUMN = "Неуспешно"


def _finished_challenges_by_user(user_challenge_df: pd.DataFrame) -> pd.DataFrame:
    """Count finished challenges per employee, split into successful vs. unsuccessful.

    Only rows with challenge_status == "finished" carry a real challenge_success value
    (True/False); everything else is still "new"/"ongoing" and is excluded here.
    """
    finished = user_challenge_df[
        (user_challenge_df["challenge_status"] == "finished")
        & (~user_challenge_df["user_id"].isin(EXCLUDED_FROM_EMPLOYEE_LIST))
    ]
    if finished.empty:
        return pd.DataFrame()

    finished = finished.copy()
    finished[_SUCCESS_COLUMN] = finished["challenge_success"] == True  # noqa: E712

    counts = (
        finished.groupby(["user_name", _SUCCESS_COLUMN])
        .size()
        .unstack(fill_value=0)
        .rename(columns={True: _SUCCESS_COLUMN, False: _FAILURE_COLUMN})
        .reindex(columns=[_SUCCESS_COLUMN, _FAILURE_COLUMN], fill_value=0)
    )
    counts["_total"] = counts.sum(axis=1)
    counts = counts.sort_values("_total", ascending=False).drop(columns="_total")
    return counts


def _bonuses_earned_by_user(earned_bonus_df: pd.DataFrame) -> pd.Series:
    """Sum bonuses earned per employee. `earned_bonus_df` is expected to already be scoped to
    a date range and to 'charge bonus' transactions server-side (see data.get_earned_bonus_df) -
    only the service-account exclusion and the user_id -> user_name mapping happen here."""
    if earned_bonus_df.empty:
        return pd.Series(dtype="int64")

    earned = earned_bonus_df[~earned_bonus_df["user_id"].isin(EXCLUDED_FROM_EMPLOYEE_LIST)]
    if earned.empty:
        return pd.Series(dtype="int64")

    id_to_name = {user_id: name for name, user_id in data.get_users_map().items()}
    totals = earned.groupby("user_id")["bonus_value"].sum()
    totals.index = totals.index.map(lambda user_id: id_to_name.get(user_id, user_id))
    totals.index.name = "user_name"
    return totals.sort_values(ascending=False)


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
    st.subheader("Статистика")

    st.markdown("#### Выполненные задания по сотрудникам")
    finished_challenges_df = _finished_challenges_by_user(data.get_user_challenge_df())
    if finished_challenges_df.empty:
        st.info("Пока никто не завершил ни одного задания.")
    else:
        st.bar_chart(finished_challenges_df, color=["#2ecc71", "#e74c3c"])

    st.divider()
    st.markdown("#### Заработанные бонусы по сотрудникам")
    selected_range = _render_bonus_range_picker()
    if selected_range is not None:
        start_date, end_date = selected_range
        earned_bonus_df = data.get_earned_bonus_df(start_date, end_date)
        bonus_totals = _bonuses_earned_by_user(earned_bonus_df)
        if bonus_totals.empty:
            st.info("За выбранный период никто не заработал бонусов.")
        else:
            st.bar_chart(bonus_totals)
