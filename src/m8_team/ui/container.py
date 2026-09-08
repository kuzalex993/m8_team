"""Build the backend :class:`Container` once per Streamlit session."""

from __future__ import annotations

import streamlit as st

from m8_team.backend.container import Container, build_container


def get_container() -> Container:
    if "container" not in st.session_state:
        st.session_state["container"] = build_container()
    return st.session_state["container"]  # type: ignore[no-any-return]
