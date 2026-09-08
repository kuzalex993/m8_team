"""'Мои настройки' page: how to connect Telegram notifications."""

from __future__ import annotations

import streamlit as st

from m8_team.ui.container import get_container


def render_settings_page() -> None:
    st.markdown(body="Для того, чтобы подключить уведомления, перейдите по ссылке в Telegram бот.")
    st.markdown("[Перейти в Телеграм web](https://web.telegram.org/k/#@EightAgencyAssist_bot)")
    st.markdown(f"[Перейти в Телеграм app]({get_container().config.bot_endpoint})")
