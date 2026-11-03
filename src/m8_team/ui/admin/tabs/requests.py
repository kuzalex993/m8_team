"""'Запросы' tab (was ``components/admin/requests_tab.py``): confirm pending reward requests
and list the decided ones.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from m8_team.backend.domain.enums import RewardStatus
from m8_team.backend.domain.errors import DomainError, RewardAlreadyResolved
from m8_team.backend.domain.models import UserReward
from m8_team.ui.common.labels import REWARD_STATUS_LABELS
from m8_team.ui.container import get_container


def _resolve_request(user_reward_id: str, *, cancel: bool) -> None:
    if st.session_state.get("user_id") != "admin":
        st.session_state["reward_decision_feedback"] = (False, "Недостаточно прав")
        return
    try:
        service = get_container().reward
        if cancel:
            service.cancel(user_reward_id=user_reward_id)
        else:
            service.confirm(user_reward_id=user_reward_id)
        message = (
            "Заявка отменена. Баллы возвращены пользователю" if cancel else "Награда подтверждена"
        )
        st.session_state["reward_decision_feedback"] = (True, message)
    except RewardAlreadyResolved:
        st.session_state["reward_decision_feedback"] = (False, "Заявка уже обработана")
    except DomainError:
        st.session_state["reward_decision_feedback"] = (
            False,
            "Не удалось обработать заявку. Проверьте резервирование и повторите попытку",
        )
    # The employee tab caches the selected employee's free balance in this session.
    selected = st.session_state.get("selected_user_name")
    selected_id = st.session_state.get("users_data_map", {}).get(selected)
    if selected_id:
        st.session_state["current_user_balance"] = get_container().user.free_bonuses(selected_id)


def confirm_user_request(user_reward_id: str) -> None:
    _resolve_request(user_reward_id, cancel=False)


def cancel_user_request(user_reward_id: str) -> None:
    _resolve_request(user_reward_id, cancel=True)


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
            st.form_submit_button(
                label="Подтвердить",
                width="stretch",
                type="primary",
                on_click=confirm_user_request,
                args=(user_reward.id,),
            )
            st.form_submit_button(
                label="Отменить",
                width="stretch",
                on_click=cancel_user_request,
                args=(user_reward.id,),
            )


def render_requests_tab() -> None:
    outcome = st.session_state.pop("reward_decision_feedback", None)
    if outcome is not None:
        ok, message = outcome
        st.success(message) if ok else st.error(message)
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
            completed_rewards_to_df["status"].append(
                REWARD_STATUS_LABELS.get(
                    user_reward.user_reward_status, user_reward.user_reward_status
                )
            )
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
                width="stretch",
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
