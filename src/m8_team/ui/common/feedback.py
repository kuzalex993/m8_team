"""Bridge between service outcomes and Streamlit toasts.

``on_click`` callbacks run before the script body reruns, so they cannot call ``st.success``
directly and have it appear in the right place. They stash the outcome here; the tab body
renders it via :func:`show_result` where the inline toast used to be.
"""

from __future__ import annotations

import streamlit as st

_OK_FLAG = "op_ok"


def mark_ok() -> None:
    st.session_state[_OK_FLAG] = True


def mark_failed() -> None:
    st.session_state[_OK_FLAG] = False


def show_result(submitted: bool, success_message: str, error_message: str) -> None:
    """Render success/error for a form whose ``on_submit`` callback called
    :func:`mark_ok` / :func:`mark_failed`, then reset."""
    if not submitted:
        return
    if st.session_state.pop(_OK_FLAG, False):
        st.success(success_message)
    else:
        st.error(error_message)
