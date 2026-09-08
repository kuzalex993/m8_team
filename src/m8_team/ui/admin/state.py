"""One-time ``session_state`` priming for the admin page (was ``components/admin/state.py``)."""

from __future__ import annotations

import streamlit as st

from m8_team.ui.common import cache
from m8_team.ui.container import get_container


def ensure_session_state() -> None:
    if "admin_state_initialized" in st.session_state:
        return

    cache.challenges_df()
    cache.rewards_df()
    cache.user_challenge_df()
    cache.users_map()

    st.session_state.bot_endpoint = get_container().config.bot_endpoint
    st.session_state.current_user_balance = None
    st.session_state.insufficient_balance_error = False
    st.session_state.additional_bonus_widget = 0

    st.session_state.admin_state_initialized = True
