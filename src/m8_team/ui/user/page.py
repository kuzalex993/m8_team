"""User page dispatcher (was ``components/userPage.py::show_user_page``)."""

from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from m8_team.ui.container import get_container
from m8_team.ui.user.pages.bonuses import render_bonuses_page
from m8_team.ui.user.pages.challenges import render_challenges_page
from m8_team.ui.user.pages.settings import render_settings_page


def show_user_page() -> None:
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = get_container().user.get_raw(st.session_state.user_id)
    if "bot_endpoint" not in st.session_state:
        st.session_state["bot_endpoint"] = get_container().config.bot_endpoint

    with st.sidebar:
        selected = option_menu(
            "M8Agency",
            ["Мои бонусы", "Мои задания", "Мои настройки"],
            icons=["award", "list-task"],
            menu_icon="cast",
            default_index=0,
        )

    if selected == "Мои бонусы":
        render_bonuses_page()
    elif selected == "Мои задания":
        render_challenges_page()
    elif selected == "Мои настройки":
        render_settings_page()
