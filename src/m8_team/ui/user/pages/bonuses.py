"""'Мои бонусы' page: balance overview, reward picker, and the user's own reward requests."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

from m8_team.backend.domain.clock import ISO_FORMAT
from m8_team.backend.domain.errors import DomainError
from m8_team.ui.common import cache
from m8_team.ui.container import get_container
from m8_team.ui.user.charts import draw_bonus_chart
from m8_team.ui.user.state import refresh_user_data


def request_reward(reward_id: str, reward_description: str, reward_price: int) -> None:
    try:
        get_container().reward.request(
            user_id=st.session_state.username,
            user_name=st.session_state.user_data["user_name"],
            reward_id=reward_id,
            reward_description=reward_description,
            reward_price=reward_price,
        )
    except DomainError:
        st.session_state["reward_request_failed"] = True
    refresh_user_data()


def _render_reward_picker() -> None:
    with st.expander("Выбрать награду", expanded=False):
        if st.session_state.pop("reward_request_failed", False):
            st.warning("Не удалось оформить запрос награды.")
        rewards_df = cache.rewards_df()
        rewards_list = rewards_df["reward_description"].tolist()
        reward_to_get = st.selectbox(
            label="Награда",
            placeholder="Выберите желаемую награду",
            key="reward_to_get",
            options=rewards_list,
            index=None,
        )
        if reward_to_get is None:
            return
        reward_id = rewards_df[rewards_df["reward_description"] == reward_to_get]["id"].values[0]
        selected_reward = rewards_df.loc[rewards_df["id"] == reward_id]
        reward_price = int(selected_reward["reward_price"].values[0])

        if st.session_state.user_data["user_free_bonuses"] >= reward_price:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Стоимость награды: **{reward_price}** баллов")
            with col2:
                st.button(
                    label="Получить награду",
                    on_click=request_reward,
                    args=(reward_id, reward_to_get, reward_price),
                    use_container_width=True,
                    type="primary",
                )
        else:
            st.warning(
                "У вас недостаточно баллов, чтобы получить награду. "
                f"Стоимость награды **{reward_price}**"
            )


def _render_requested_rewards() -> None:
    with st.expander("Запрошенные награды", expanded=False):
        to_rewards_df: dict[str, list[Any]] = {"description": [], "request_date": [], "status": []}
        for reward in get_container().reward.requests(st.session_state.username):
            to_rewards_df["description"].append(reward.reward_description)
            to_rewards_df["request_date"].append(
                datetime.strptime(reward.user_reward_request_date, ISO_FORMAT)
            )
            to_rewards_df["status"].append(reward.user_reward_status)
        rewards_df = pd.DataFrame(to_rewards_df).sort_values(by="request_date", ascending=False)
        st.dataframe(
            data=rewards_df,
            use_container_width=True,
            hide_index=True,
            column_order=["description", "request_date", "status"],
            column_config={
                "description": st.column_config.Column(label="Награда"),
                "request_date": st.column_config.DatetimeColumn(label="Дата запроса"),
                "status": st.column_config.Column(label="Статус запроса"),
            },
        )


def render_bonuses_page() -> None:
    st.session_state["user_data"] = get_container().user.get_raw(st.session_state["user_id"])
    user_data = st.session_state.user_data

    with st.container(height=300, border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.header(user_data["user_name"], anchor=None, help=None, divider=False)
            st.markdown(f"**Позиция:** {user_data['user_position']}", help=None)
            st.markdown(f"**Доступные бонусы:** {user_data['user_free_bonuses']}", help=None)
            st.markdown(f"**Бонусы в резерве:** {user_data['user_reserved_bonuses']}", help=None)
        with col2:
            st_echarts(
                options=draw_bonus_chart(
                    user_data["user_free_bonuses"], user_data["user_reserved_bonuses"]
                ),
                height="250px",
            )

    _render_reward_picker()
    _render_requested_rewards()
