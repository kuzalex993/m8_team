"""Shared scaffolding for the "add new item" / "edit existing item" expanders used by the
Задания and Награды tabs. Both tabs previously duplicated the same
expander -> form -> submit -> success/error-toast flow almost verbatim; this module keeps
that flow in one place while leaving the entity-specific fields to the caller.
"""

from collections.abc import Callable

import streamlit as st


def show_submit_feedback(submitted: bool, success_message: str, error_message: str) -> None:
    """Render the success/error toast for a form submitted via an on_click callback that
    sets st.session_state.transaction_status, then reset the flag."""
    if not submitted:
        return
    if st.session_state.transaction_status:
        st.success(success_message)
        st.session_state.transaction_status = False
    else:
        st.error(error_message)


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
        show_submit_feedback(submitted, success_message, error_message)


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
            show_submit_feedback(submitted, success_message, error_message)
