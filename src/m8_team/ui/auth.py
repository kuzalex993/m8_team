"""streamlit-authenticator wiring. Ported from the top of the old ``main.py``."""

from __future__ import annotations

from typing import Any

import streamlit as st
import streamlit_authenticator as stauth

from m8_team.ui.container import get_container


def load_users_config() -> dict[str, Any]:
    if st.session_state.get("users_config") is None:
        st.session_state["users_config"] = get_container().auth.load_config()
    return st.session_state["users_config"]  # type: ignore[no-any-return]


def build_authenticator(users_config: dict[str, Any]) -> stauth.Authenticate:
    return stauth.Authenticate(
        users_config["credentials"],
        users_config["cookie"]["name"],
        users_config["cookie"]["key"],
        users_config["cookie"]["expiry_days"],
    )


def render_registration(authenticator: stauth.Authenticate) -> None:
    """Registration expander: write the auth config back and create the ``users`` doc."""
    container = get_container()
    with st.expander(label="Зарегистрироваться"):
        try:
            email, username, name = authenticator.register_user(
                location="main", preauthorization=False
            )
            if email:
                registered = container.auth.persist_registration(
                    st.session_state.users_config
                ) and container.user.create_employee(email=email, username=username, name=name)
                if registered:
                    st.success("Пользователь успешно зарегистрирован")
                else:
                    st.error("Could not register user")
        except Exception as exc:  # noqa: BLE001 - surface any auth-lib error to the user
            st.error(exc)
