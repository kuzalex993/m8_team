"""Session-state caching over service reads.

Replaces ``components/admin/data.py``: whole-collection listings are fetched once into
``st.session_state`` and only re-read when a caller passes ``force_refresh=True`` after a
mutation. Caching is a UI concern - services and repositories stay stateless.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from m8_team.ui.container import get_container


def challenges_df(*, force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or "challenge_df" not in st.session_state:
        rows = get_container().challenge.list_catalogue()
        for row in rows:
            row["challenge_date_update"] = str(row["challenge_date_update"])
        st.session_state.challenge_df = pd.DataFrame(rows)
    return st.session_state.challenge_df


def rewards_df(*, force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or "rewards_df" not in st.session_state:
        st.session_state.rewards_df = pd.DataFrame(get_container().reward.list_catalogue())
    return st.session_state.rewards_df


def user_challenge_df(*, force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or "user_challenge_df" not in st.session_state:
        st.session_state.user_challenge_df = pd.DataFrame(
            get_container().challenge.list_all_assignments()
        )
    return st.session_state.user_challenge_df


def users_map(*, force_refresh: bool = False) -> dict[str, str]:
    if force_refresh or "users_data_map" not in st.session_state:
        st.session_state.users_data_map = get_container().user.employee_map()
    return st.session_state.users_data_map  # type: ignore[no-any-return]


def earned_bonus_rows(
    start: date, end: date, *, force_refresh: bool = False
) -> list[dict[str, Any]]:
    """``charge bonus`` ledger rows for [start, end], re-fetched only when the range
    changes (mirrors the old ``admin/data.py::get_earned_bonus_df`` range-keyed cache)."""
    range_key = (start, end)
    if force_refresh or st.session_state.get("earned_bonus_range_key") != range_key:
        st.session_state.earned_bonus_rows = get_container().stats.earned_bonus_rows(start, end)
        st.session_state.earned_bonus_range_key = range_key
    return st.session_state.earned_bonus_rows  # type: ignore[no-any-return]
