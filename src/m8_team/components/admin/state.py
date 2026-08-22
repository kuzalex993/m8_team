"""One-time session_state initialization for the admin page: primes the cached data.py
lookups and sets the widget/UI-flag defaults the tabs expect to already exist."""

import os

import streamlit as st

from . import data


def ensure_session_state() -> None:
    """Populate every session_state key the admin page relies on, once per session."""
    if "admin_state_initialized" in st.session_state:
        return

    data.get_challenges_df()
    data.get_rewards_df()
    data.get_user_challenge_df()
    data.get_users_map()

    st.session_state.transaction_status = False
    st.session_state.bot_endpoint = os.getenv("T_BOT_ENDPOINT")
    st.session_state.current_user_balance = None
    st.session_state.insufficient_balance_error = False
    st.session_state.additional_bonus_widget = 0

    st.session_state.admin_state_initialized = True
