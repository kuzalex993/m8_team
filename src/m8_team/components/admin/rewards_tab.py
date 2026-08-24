"""'Награды' tab: add/edit rewards and browse the full reward list. Mirrors tasks_tab.py's
structure - same crud.py flow, different fields and Firestore collection."""

from datetime import datetime

import streamlit as st

from m8_team.components.firebase import add_new_document, update_document

from . import data
from .constants import REWARDS_COLLECTION
from .crud import render_add_expander, render_edit_expander


def add_new_reward() -> None:
    new_reward = {
        "reward_description": st.session_state.reward_description_widget,
        "reward_price": st.session_state.reward_price_widget,
        "reward_last_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    if add_new_document(collection_name=REWARDS_COLLECTION, document_data=new_reward):
        st.session_state.transaction_status = True
    data.get_rewards_df(force_refresh=True)


def update_reward(reward_id: str) -> None:
    edited_reward = {
        "reward_description": st.session_state.edit_reward_description_widget,
        "reward_price": st.session_state.edit_reward_price_widget,
        "reward_last_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    if update_document(
        collection_name=REWARDS_COLLECTION, document_id=reward_id, document_data=edited_reward
    ):
        st.session_state.transaction_status = True
    data.get_rewards_df(force_refresh=True)


def _render_add_reward_fields() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.text_area(
            label="Награда",
            key="reward_description_widget",
            placeholder="Добавьте описание награды",
            max_chars=200,
        )
    with col2:
        st.number_input(
            label="Стоимость награды",
            key="reward_price_widget",
            min_value=0,
            value=None,
            step=1,
            placeholder="Введите количество баллов",
        )


def _render_edit_reward_fields(reward_to_edit: str | None) -> str | None:
    rewards_df = data.get_rewards_df()
    reward_id = None
    col1, col2 = st.columns(2)
    with col1:
        if reward_to_edit is None:
            reward_description_to_edit = ""
            reward_price_to_edit = None
        else:
            reward_id = rewards_df[rewards_df["reward_description"] == reward_to_edit]["id"].values[
                0
            ]
            selected_reward = rewards_df.loc[rewards_df["id"] == reward_id]
            reward_description_to_edit = selected_reward["reward_description"].values[0]
            reward_price_to_edit = int(selected_reward["reward_price"].values[0])
        st.text_area(
            value=reward_description_to_edit,
            label="Новая награда",
            key="edit_reward_description_widget",
            placeholder="Новое опасание награды",
            max_chars=200,
        )
    with col2:
        st.number_input(
            value=reward_price_to_edit,
            label="Новая стоимость награды",
            key="edit_reward_price_widget",
            min_value=0,
            step=1,
            placeholder="Введите количество баллов",
        )
    return reward_id


def render_rewards_tab() -> None:
    st.subheader("Управление наградами")

    render_add_expander(
        title="Добавить новую награду :new:",
        form_key="add_reward_form",
        render_fields=_render_add_reward_fields,
        on_submit=add_new_reward,
        submit_label="Добавить награду в базу",
        success_message="Новая награда успешно создана",
        error_message="Не удалось создать новую награду",
    )

    rewards_df = data.get_rewards_df()
    rewards_list = rewards_df["reward_description"].tolist()
    render_edit_expander(
        title="Редактирование награды :pencil2:",
        select_label="Награда",
        select_placeholder="Выберите награду для изменения",
        select_key="reward_to_edit",
        options=rewards_list,
        form_key="edit_reward_form",
        render_fields=_render_edit_reward_fields,
        on_submit=update_reward,
        submit_label="Применить изменения",
        success_message="Награда успешно обновлена",
        error_message="Не удалось обновить награду",
    )

    with st.expander(label="База наград :books:"):
        st.dataframe(
            data.get_rewards_df(),
            use_container_width=False,
            column_order=("reward_description", "reward_price", "reward_last_update"),
            column_config={
                "reward_description": "Описание награды",
                "reward_price": st.column_config.NumberColumn(
                    label="Стоимость награды", help="Стоимость в баллах", format="%d"
                ),
                "reward_last_update": st.column_config.DateColumn(
                    label="Дата обновления",
                    help="Дата, когда награда была обновлена последний раз",
                    format="DD.MM.YYYY",
                ),
            },
            hide_index=True,
        )
