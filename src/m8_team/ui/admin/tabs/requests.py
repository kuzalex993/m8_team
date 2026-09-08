"""'Запросы' tab (was ``components/admin/requests_tab.py``): confirm pending reward requests
and list the decided ones.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from m8_team.backend.domain.enums import RewardStatus
from m8_team.backend.domain.errors import DomainError
from m8_team.backend.domain.models import UserReward
from m8_team.ui.common import feedback
from m8_team.ui.container import get_container


def confirm_user_request(user_reward_id: str, user_id: str, reward_id: str) -> None:
    try:
        get_container().reward.confirm(
            user_reward_id=user_reward_id, user_id=user_id, reward_id=reward_id
        )
        feedback.mark_ok()
    except DomainError:
        feedback.mark_failed()


def _render_pending_request(user_reward: UserReward) -> None:
    with st.form(f"request_form_{user_reward.id}"):
        request_col1, request_col2, request_col3, request_col4 = st.columns([2, 1, 1, 1])
        date_object = datetime.fromisoformat(
            user_reward.user_reward_request_date.replace("Z", "+00:00")
        )
        formatted_date = date_object.strftime("%d/%m/%Y")
        with request_col1:
            st.markdown(body=user_reward.reward_description)
        with request_col2:
            st.caption(body=user_reward.user_name)
        with request_col3:
            st.caption(body=formatted_date)
        with request_col4:
            submitted = st.form_submit_button(
                label="Подтвердить",
                use_container_width=True,
                type="primary",
                on_click=confirm_user_request,
                args=(user_reward.id, user_reward.user_id, user_reward.reward_id),
            )
        feedback.show_result(
            submitted,
            success_message=f"Награда «{user_reward.reward_description}» подтверждена",
            error_message="Не удалось подтвердить: недостаточно зарезервированных бонусов",
        )


def render_requests_tab() -> None:
    completed_rewards_to_df: dict[str, list[Any]] = {
        "name": [],
        "description": [],
        "request_date": [],
        "status": [],
        "decision_date": [],
    }
    show_info_flag = True
    info_messages = ["Ого! Кажется, пока тут пусто...", "И тут тоже пусто..."]

    for user_reward in get_container().reward.requests("all"):
        if user_reward.user_reward_status == RewardStatus.NEW:
            show_info_flag = False
            _render_pending_request(user_reward)
        else:
            completed_rewards_to_df["description"].append(user_reward.reward_description)
            completed_rewards_to_df["name"].append(user_reward.user_name)
            completed_rewards_to_df["request_date"].append(user_reward.user_reward_request_date)
            completed_rewards_to_df["status"].append(user_reward.user_reward_status)
            completed_rewards_to_df["decision_date"].append(user_reward.user_reward_decision_date)

    if show_info_flag:
        st.info(info_messages[0])
        info_messages.pop(0)

    with st.expander("Остальные запросы"):
        if len(completed_rewards_to_df["description"]) == 0:
            st.info(info_messages[0])
        else:
            completed_rewards_df = pd.DataFrame(completed_rewards_to_df).sort_values(
                by="request_date", ascending=False
            )
            st.dataframe(
                completed_rewards_df,
                use_container_width=True,
                column_order=("description", "name", "request_date", "status", "decision_date"),
                column_config={
                    "description": "Описание награды",
                    "name": "Имя",
                    "request_date": st.column_config.DateColumn(
                        label="Дата запроса", format="DD.MM.YYYY"
                    ),
                    "status": "Статус запроса",
                    "decision_date": st.column_config.DateColumn(
                        label="Дата принятия решения", format="DD.MM.YYYY"
                    ),
                },
                hide_index=True,
            )
