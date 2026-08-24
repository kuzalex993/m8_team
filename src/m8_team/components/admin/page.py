"""Entry point for the admin page: renders the sidebar menu and dispatches to the selected
tab's render function. Add a new tab by extending MENU_ITEMS and _TAB_RENDERERS."""

import streamlit as st
from streamlit_option_menu import option_menu

from .constants import MENU_ITEMS
from .employees_tab import render_employees_tab
from .requests_tab import render_requests_tab
from .rewards_tab import render_rewards_tab
from .state import ensure_session_state
from .stats_tab import render_stats_tab
from .tasks_tab import render_tasks_tab

_TAB_RENDERERS = {
    "Сотрудники": render_employees_tab,
    "Задания": render_tasks_tab,
    "Награды": render_rewards_tab,
    "Запросы": render_requests_tab,
    "Статистика": render_stats_tab,
}


def show_admin_page() -> None:
    ensure_session_state()

    with st.sidebar:
        selected = option_menu(
            "M8.Agenсy",
            [item.label for item in MENU_ITEMS],
            icons=[item.icon for item in MENU_ITEMS],
            menu_icon="cast",
            default_index=0,
        )

    render_tab = _TAB_RENDERERS.get(selected)
    if render_tab is not None:
        render_tab()
