"""Shared session helpers for the user pages."""

from __future__ import annotations

import streamlit as st

from m8_team.ui.container import get_container


def refresh_user_data() -> None:
    st.session_state.user_data = get_container().user.get_raw(st.session_state.user_id)
