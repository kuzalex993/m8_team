"""'Запросы' tab: confirm pending reward requests and list the already-decided ones."""

import logging
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from m8_team.components.firebase import (
    add_new_document,
    get_user_rewards,
    get_value,
    update_document,
)
from m8_team.components.models import UserReward

from .constants import (
    REWARDS_COLLECTION,
    USER_BONUS_COLLECTION,
    USER_REWARD_COLLECTION,
    USERS_COLLECTION,
)
from .crud import show_submit_feedback
from .notify import notify_user

logger = logging.getLogger(__name__)


def confirm_user_request(user_reward_id: str, user_id: str, reward_id: str) -> None:
    st.session_state.transaction_status = False
    reward_price = get_value(
        collection_name=REWARDS_COLLECTION, document_name=reward_id, field_name="reward_price"
    )
    reward_description = get_value(
        collection_name=REWARDS_COLLECTION, document_name=reward_id, field_name="reward_description"
    )
    user_reserved_bonus = get_value(
        collection_name=USERS_COLLECTION, document_name=user_id, field_name="user_reserved_bonuses"
    )
    if reward_price > user_reserved_bonus:
        logger.error("Error! Lack of reserved bonuses")
        return

    updated_user_data = {"user_reserved_bonuses": user_reserved_bonus - reward_price}
    update_document(
        collection_name=USERS_COLLECTION, document_id=user_id, document_data=updated_user_data
    )

    updated_user_reward_data = {
        "user_reward_status": "completed",
        "user_reward_decision_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    update_document(
        collection_name=USER_REWARD_COLLECTION,
        document_id=user_reward_id,
        document_data=updated_user_reward_data,
    )

    new_user_bonus_record = {
        "user_id": user_id,
        "transaction_type": "debiting bonus",
        "event_type": "user_reward",
        "event_id": user_reward_id,
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "bonus_value": reward_price,
    }
    add_new_document(collection_name=USER_BONUS_COLLECTION, document_data=new_user_bonus_record)
    notify_user(message=f"Ура! Админ подтвердил награду: {reward_description}", user_name=user_id)
    st.session_state.transaction_status = True


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
        show_submit_feedback(
            submitted,
            success_message=f"Награда «{user_reward.reward_description}» подтверждена",
            error_message="Не удалось подтвердить: недостаточно зарезервированных бонусов",
        )


def render_requests_tab() -> None:
    user_rewards = get_user_rewards(user_id="all")
    completed_rewards_to_df: dict[str, list[Any]] = {
        "name": [],
        "description": [],
        "request_date": [],
        "status": [],
        "decision_date": [],
    }
    show_info_flag = True
    info_messages = ["Ого! Кажется, пока тут пусто...", "И тут тоже пусто..."]

    for doc in user_rewards:
        doc_data = doc.to_dict()
        if doc_data is None:
            continue
        user_reward = UserReward.from_dict(doc_data, doc.id)
        if user_reward.user_reward_status == "new":
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
