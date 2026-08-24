"""'Задания' tab: add/edit challenges and browse the full challenge list. Add/edit UI flow
is built on crud.py; only the field layout and Firestore writes are specific to this tab."""

from datetime import datetime

import streamlit as st

from m8_team.components.firebase import add_new_document, update_document

from . import data
from .constants import CHALLENGES_COLLECTION
from .crud import render_add_expander, render_edit_expander


def add_new_challenge() -> None:
    new_task = {
        "challenge_description": st.session_state.task_description_widget,
        "challenge_reward": st.session_state.task_award_widget,
        "challenge_planned_time_completion": st.session_state.task_planned_time_widget,
        "challenge_active": True,
        "challenge_date_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    if add_new_document(collection_name=CHALLENGES_COLLECTION, document_data=new_task):
        st.session_state.transaction_status = True
    data.get_challenges_df(force_refresh=True)


def update_challenge(challenge_id: str) -> None:
    edited_task = {
        "challenge_description": st.session_state.edit_challenge_description_widget,
        "challenge_reward": st.session_state.edit_challenge_reward_widget,
        "challenge_planned_time_completion": st.session_state.edit_challenge_planned_time_widget,
        "challenge_active": True,
        "challenge_date_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    if update_document(
        collection_name=CHALLENGES_COLLECTION, document_id=challenge_id, document_data=edited_task
    ):
        st.session_state.transaction_status = True
    data.get_challenges_df(force_refresh=True)


def _render_add_challenge_fields() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.text_area(
            label="Задания",
            key="task_description_widget",
            placeholder="Сформулируйте задание",
            max_chars=200,
            height=120,
        )
    with col2:
        st.number_input(
            label="Награда за выполнение",
            key="task_award_widget",
            min_value=0,
            value=None,
            step=1,
            placeholder="Введите количество баллов",
        )
        st.number_input(
            label="Время на выполнение",
            key="task_planned_time_widget",
            min_value=0,
            value=None,
            step=1,
            placeholder="Введите количестов дней...",
        )


def _render_edit_challenge_fields(task_to_edit: str | None) -> str | None:
    challenges_df = data.get_challenges_df()
    challenge_id = None
    col1, col2 = st.columns(2)
    with col1:
        if task_to_edit is None:
            task_description_to_edit = ""
            task_award_to_edit = None
            task_planned_time_to_edit = None
        else:
            challenge_id = challenges_df[challenges_df["challenge_description"] == task_to_edit][
                "id"
            ].values[0]
            selected_challenge = challenges_df.loc[challenges_df["id"] == challenge_id]
            task_description_to_edit = selected_challenge["challenge_description"].values[0]
            task_award_to_edit = int(selected_challenge["challenge_reward"].values[0])
            task_planned_time_to_edit = int(
                selected_challenge["challenge_planned_time_completion"].values[0]
            )
        st.text_area(
            value=task_description_to_edit,
            label="Новое задание",
            key="edit_challenge_description_widget",
            placeholder="Описание задания",
            max_chars=200,
            height=120,
        )
    with col2:
        st.number_input(
            value=task_award_to_edit,
            label="Новая награда за выполнение",
            key="edit_challenge_reward_widget",
            min_value=0,
            step=1,
            placeholder="Введите количество баллов",
        )
        st.number_input(
            value=task_planned_time_to_edit,
            label="Новое время на выполнение",
            key="edit_challenge_planned_time_widget",
            min_value=0,
            step=1,
            placeholder="Введите количестов дней...",
        )
    return challenge_id


def render_tasks_tab() -> None:
    st.subheader("Управление заданиями")

    render_add_expander(
        title="Добавление заданий в базу данных :new:",
        form_key="add_challenge_form",
        render_fields=_render_add_challenge_fields,
        on_submit=add_new_challenge,
        submit_label="Добавить задание в базу",
        success_message="Новое задание успешно создано",
        error_message="Не удалось создать новое задание",
    )

    challenges_df = data.get_challenges_df()
    challenges_list = challenges_df["challenge_description"].tolist()
    render_edit_expander(
        title="Редактирование задания :pencil2:",
        select_label="Задание",
        select_placeholder="Выберите задание для изменения",
        select_key="challenge_to_edit",
        options=challenges_list,
        form_key="edit_challenge_form",
        render_fields=_render_edit_challenge_fields,
        on_submit=update_challenge,
        submit_label="Применить изменения",
        success_message="Задание успешно обновлено",
        error_message="Не удалось обновить задание",
    )

    with st.expander(label="База заданий :books:"):
        st.dataframe(
            data.get_challenges_df(),
            use_container_width=False,
            column_order=(
                "challenge_description",
                "challenge_reward",
                "challenge_planned_time_completion",
                "challenge_active",
                "challenge_date_update",
            ),
            column_config={
                "challenge_description": "Описание задания",
                "challenge_reward": st.column_config.NumberColumn(
                    label="Награда", help="Баллы за выполение задания", format="%d"
                ),
                "challenge_planned_time_completion": st.column_config.NumberColumn(
                    label="Время на выполнение",
                    help="Количество дней, отведенное на выполнение задания",
                    format="%d",
                ),
                "challenge_active": st.column_config.CheckboxColumn(
                    label="Задание в списке?",
                    help="Здесь можно задание сделать доступным для выбора",
                    default=False,
                ),
                "challenge_date_update": st.column_config.DateColumn(
                    label="Дата обновления",
                    help="Дата, когда задание было обновлено последний раз",
                    format="DD.MM.YYYY",
                ),
            },
            hide_index=True,
        )
