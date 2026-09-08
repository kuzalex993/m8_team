"""Streamlit entrypoint. Ported from the old ``src/m8_team/main.py``.

Loads the auth config, renders login + registration, and routes ``admin`` to the admin page
and everyone else to the user page.
"""

from __future__ import annotations

import streamlit as st

from m8_team.ui.admin.page import show_admin_page
from m8_team.ui.auth import build_authenticator, load_users_config, render_registration
from m8_team.ui.user.page import show_user_page

st.set_page_config(page_title="M8 team", layout="wide", initial_sidebar_state="auto")

st.session_state.setdefault("user_name", None)
st.session_state.setdefault("user_id", None)

users_config = load_users_config()
authenticator = build_authenticator(users_config)

st.session_state["user_name"], authentication_status, st.session_state["user_id"] = (
    authenticator.login(
        location="main",
        fields={
            "Form name": "Войти в аккаунт",
            "Username": "Имя пользователя",
            "Password": "Пароль",
            "Login": "Войти",
        },
    )
)

if not authentication_status:
    st.error("Имя пользователя и/или пароль введены неверно!")
elif authentication_status is None:
    st.warning("Введите имя пользователя и пароль...")

if authentication_status is not True:
    render_registration(authenticator)

if authentication_status is True:
    if st.session_state["user_id"] == "admin":
        show_admin_page()
    else:
        show_user_page()
    authenticator.logout(button_name="Выйти", location="sidebar")
