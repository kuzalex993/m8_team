"""'Сотрудники' tab (was ``components/admin/employees_tab.py``): pick an employee, then
adjust their balance or assign a challenge. All writes go through ``bonus`` / ``challenge``
services.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import cast

import streamlit as st

from m8_team.backend.domain.errors import DomainError, InsufficientBalance
from m8_team.ui.common import cache, feedback
from m8_team.ui.common.labels import OPERATION_LABELS
from m8_team.ui.container import get_container


def new_user_selected() -> None:
    if st.session_state.selected_user_name:
        selected_user_id = st.session_state["users_data_map"][
            st.session_state["selected_user_name"]
        ]
        st.session_state["current_user_balance"] = get_container().user.free_bonuses(
            selected_user_id
        )


def update_user_bonus(user_id: str) -> None:
    amount = int(st.session_state.additional_bonus_widget)
    transaction_type = OPERATION_LABELS[st.session_state.operation_widget]
    try:
        get_container().bonus.admin_adjust(
            user_id=user_id, amount=amount, transaction_type=transaction_type
        )
        feedback.mark_ok()
        st.session_state.additional_bonus_widget = 0
    except InsufficientBalance:
        st.session_state.insufficient_balance_error = True
    except DomainError:
        feedback.mark_failed()
    st.session_state.current_user_balance = get_container().user.free_bonuses(user_id)


def add_new_user_challenge(challenge_id: int, challenge_duration: int) -> None:
    if not st.session_state.selected_user_name:
        return
    selected_user_id = st.session_state.users_data_map[st.session_state.selected_user_name]
    ok = get_container().challenge.assign(
        user_id=selected_user_id,
        user_name=st.session_state.selected_user_name,
        challenge_id=challenge_id,
        description=st.session_state.challenge_to_assign_description_widget,
        start_date=st.session_state.challenge_to_assign_start_date_widget,
        duration=challenge_duration,
    )
    feedback.mark_ok() if ok else feedback.mark_failed()
    if ok:
        cache.user_challenge_df(force_refresh=True)


def _render_bonus_management_tab(selected_user_id: str, selected_user_name: str) -> None:
    with st.container():
        col1, col2 = st.columns(2)
        additional_bonus = 0
        with col1:
            additional_bonus = int(
                st.number_input(
                    label="Бонусы",
                    min_value=0,
                    placeholder="Введите количество бонусов",
                    key="additional_bonus_widget",
                )
            )
            operation = st.radio(
                label="Операция",
                options=["Добавить", "Вычесть"],
                horizontal=True,
                key="operation_widget",
            )
            if operation == "Вычесть":
                additional_bonus *= -1
        with col2:
            st.metric(
                label="Текущий баланс",
                value=st.session_state.current_user_balance,
                delta=None if additional_bonus == 0 else additional_bonus,
                delta_color="normal",
                help=None,
                label_visibility="visible",
            )
        if st.session_state.current_user_balance + additional_bonus < 0:
            st.warning("Недостаточно текущего баланса для совершения операции")
        else:
            add_bonus = st.button(
                "Изменить баланс",
                on_click=update_user_bonus,
                args=(selected_user_id,),
                use_container_width=True,
                type="primary",
            )
            if add_bonus:
                if st.session_state.insufficient_balance_error:
                    st.warning("Недостаточно бонусов для списания")
                    st.session_state.insufficient_balance_error = False
                else:
                    feedback.show_result(
                        True,
                        f"Баланс пользователя {selected_user_name} обновлен",
                        "Не удалось обновить баланс",
                    )


def _render_challenge_assignment_tab(selected_user_name: str) -> None:
    challenge_df = cache.challenges_df()
    challenges_list = challenge_df["challenge_description"].tolist()
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    selected_challenge = None
    with col1:
        challenge_to_assign = st.selectbox(
            label="Задание",
            placeholder="Выберите задание",
            key="challenge_to_assign_description_widget",
            options=challenges_list,
            index=0,
        )
        challenge_id = challenge_df[challenge_df["challenge_description"] == challenge_to_assign][
            "id"
        ].values[0]
        selected_challenge = challenge_df.loc[challenge_df["id"] == challenge_id]
        challenge_duration = int(selected_challenge["challenge_planned_time_completion"].values[0])
        challenge_reward = int(selected_challenge["challenge_reward"].values[0])
    with col2:
        raw_date = st.date_input(
            label="Дата начала",
            key="challenge_to_assign_start_date_widget",
            format="DD/MM/YYYY",
        )
        start_date = cast(date, raw_date)
    with col3:
        st.date_input(
            label="Дата окончания",
            disabled=True,
            value=start_date + timedelta(days=challenge_duration),
            format="DD/MM/YYYY",
        )
    with col4:
        st.number_input(label="Бонусы", value=challenge_reward, disabled=True)

    if selected_challenge is not None:
        assign_challenge_btn = st.button(
            label="Назначить задание",
            use_container_width=True,
            type="primary",
            on_click=add_new_user_challenge,
            args=(challenge_id, challenge_duration),
        )
        feedback.show_result(
            assign_challenge_btn,
            f"Задание **{challenge_to_assign}** назначено пользователю **{selected_user_name}**",
            "Не удалось назначить задание",
        )

    st.divider()
    with st.container():
        user_challenge_df = cache.user_challenge_df()
        current_user_challenge_df = user_challenge_df.loc[
            (user_challenge_df["user_name"] == selected_user_name)
            & (user_challenge_df["challenge_status"] != "complete")
        ]
        if current_user_challenge_df.shape[0] == 0:
            st.info(f"Пользователь {selected_user_name} пока не имеет открытых заданий")
        else:
            st.dataframe(
                current_user_challenge_df,
                use_container_width=False,
                column_order=(
                    "challenge_descripion",
                    "start_date",
                    "planned_finish_date",
                    "challenge_status",
                    "fact_finish_date",
                    "challenge_success",
                ),
                column_config={
                    "challenge_descripion": "Описание задания",
                    "start_date": st.column_config.DateColumn(
                        label="Дата начала", format="DD/MM/YYYY"
                    ),
                    "planned_finish_date": st.column_config.DateColumn(
                        label="Дата окончания", format="DD/MM/YYYY"
                    ),
                    "challenge_status": st.column_config.TextColumn(
                        label="Статус задания", default="False"
                    ),
                    "fact_finish_date": st.column_config.DateColumn(
                        label="Фактическая дата завершения", format="DD.MM.YYYY"
                    ),
                    "challenge_success": st.column_config.TextColumn(
                        label="Успех прохождения", default="False"
                    ),
                },
                hide_index=True,
            )


def render_employees_tab() -> None:
    st.subheader("Сотрудники")
    users_map = cache.users_map(force_refresh=True)
    users_list = list(users_map.keys())
    selected_user_name = st.selectbox(
        label="Cотрудник",
        index=None,
        placeholder="Выберите сотрудника",
        key="selected_user_name",
        on_change=new_user_selected,
        options=users_list,
    )
    if not selected_user_name:
        return

    selected_user_id = users_map[selected_user_name]
    tab1, tab2 = st.tabs(
        ["📈 Управление бонусами пользователей", "🗃 Управление заданиями пользователей"]
    )
    with tab1:
        _render_bonus_management_tab(selected_user_id, selected_user_name)
    with tab2:
        _render_challenge_assignment_tab(selected_user_name)
