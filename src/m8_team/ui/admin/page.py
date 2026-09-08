"""Admin page dispatcher (was ``components/admin/page.py``). Add a tab by extending
``MENU_ITEMS`` and ``_TAB_RENDERERS``.
"""

from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from m8_team.ui.admin.menu import MENU_ITEMS
from m8_team.ui.admin.state import ensure_session_state
from m8_team.ui.admin.tabs.employees import render_employees_tab
from m8_team.ui.admin.tabs.requests import render_requests_tab
from m8_team.ui.admin.tabs.rewards import render_rewards_tab
from m8_team.ui.admin.tabs.stats import render_stats_tab
from m8_team.ui.admin.tabs.tasks import render_tasks_tab

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
