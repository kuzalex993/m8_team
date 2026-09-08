"""Shared 'add item' / 'edit item' expander scaffolding for the Задания and Награды tabs
(was ``components/admin/crud.py``). Pure Streamlit; the ``on_submit`` callback is expected
to call :func:`m8_team.ui.common.feedback.mark_ok` / ``mark_failed``.
"""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from m8_team.ui.common.feedback import show_result


def render_add_expander(
    *,
    title: str,
    form_key: str,
    render_fields: Callable[[], None],
    on_submit: Callable[[], None],
    submit_label: str,
    success_message: str,
    error_message: str,
    expanded: bool = True,
) -> None:
    with st.expander(label=title, expanded=expanded), st.form(form_key):
        render_fields()
        submitted = st.form_submit_button(
            label=submit_label, on_click=on_submit, use_container_width=True, type="primary"
        )
        show_result(submitted, success_message, error_message)


def render_edit_expander(
    *,
    title: str,
    select_label: str,
    select_placeholder: str,
    select_key: str,
    options: list[str],
    form_key: str,
    render_fields: Callable[[str | None], str | None],
    on_submit: Callable[[str], None],
    submit_label: str,
    success_message: str,
    error_message: str,
) -> None:
    with st.expander(label=title):
        selected = st.selectbox(
            label=select_label,
            placeholder=select_placeholder,
            key=select_key,
            options=options,
            index=None,
        )
        with st.form(form_key):
            item_id = render_fields(selected)
            submitted = st.form_submit_button(
                label=submit_label,
                on_click=on_submit,
                args=(item_id,),
                use_container_width=True,
                type="primary",
            )
            show_result(submitted, success_message, error_message)
