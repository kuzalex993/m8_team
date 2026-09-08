"""'Мои задания' page: pick a new challenge, and complete assigned ones."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import cast

import streamlit as st

from m8_team.backend.domain.clock import DATE_FORMAT
from m8_team.backend.domain.enums import ChallengeStatus
from m8_team.backend.domain.models import UserChallenge
from m8_team.ui.common import cache
from m8_team.ui.container import get_container
from m8_team.ui.user.state import refresh_user_data


@st.experimental_dialog("Задание закрыто")  # type: ignore[attr-defined]
def _completion_dialog(message: str) -> None:
    st.write(message)


def add_new_user_challenge(challenge_id: int, challenge_duration: int) -> None:
    get_container().challenge.assign(
        user_id=st.session_state.username,
        user_name=st.session_state.user_data["user_name"],
        challenge_id=challenge_id,
        description=st.session_state.challenge_to_assign_description_widget,
        start_date=st.session_state.challenge_to_assign_start_date_widget,
        duration=challenge_duration,
        notify=False,
    )


def close_user_challenge(user_challenge_id: str) -> None:
    result = get_container().challenge.complete(
        user_challenge_id=user_challenge_id,
        user_id=st.session_state.username,
        planned_finish=st.session_state["panned_finish_" + user_challenge_id],
    )
    if result.on_time:
        _completion_dialog(f"Задание закрыто вовремя. Начислено {result.reward_granted} бонусов")
    else:
        _completion_dialog(
            "Очень жаль, но бонусы не будут начислены. Задание закрыто с опозданием."
        )
    refresh_user_data()


def _render_new_challenge_picker() -> None:
    with st.expander("Выбрать новое задание", expanded=False):
        challenge_df = cache.challenges_df()
        challenges_list = challenge_df["challenge_description"].tolist()
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            challenge_to_assign = st.selectbox(
                label="Задание",
                placeholder="Выберите задание",
                key="challenge_to_assign_description_widget",
                options=challenges_list,
                index=0,
            )
            challenge_id = challenge_df[
                challenge_df["challenge_description"] == challenge_to_assign
            ]["id"].values[0]
            selected_challenge = challenge_df.loc[challenge_df["id"] == challenge_id]
            challenge_duration = int(
                selected_challenge["challenge_planned_time_completion"].values[0]
            )
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
            st.button(
                label="Назначить задание",
                use_container_width=True,
                type="primary",
                on_click=add_new_user_challenge,
                args=(challenge_id, challenge_duration),
            )


def _render_challenge_form(user_challenge: UserChallenge, *, is_new: bool) -> None:
    with st.form(f"challenge_form_{user_challenge.id}"):
        if is_new:
            st.markdown(body=f"**:new:** {user_challenge.description}")
            st.caption(body=f"Задание добавленo: {user_challenge.challenge_creation_date}")
        else:
            st.markdown(body=user_challenge.description)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.date_input(
                label="Начало",
                value=datetime.strptime(user_challenge.start_date, DATE_FORMAT),
                format="DD/MM/YYYY",
                key=f"start_{user_challenge.id}",
                disabled=True,
            )
        with col2:
            end_date = (
                datetime.strptime(user_challenge.planned_finish_date, DATE_FORMAT)
                if user_challenge.planned_finish_date
                else None
            )
            st.date_input(
                label="Окончание",
                value=end_date,
                format="DD/MM/YYYY",
                key=f"panned_finish_{user_challenge.id}",
                disabled=True,
            )
        st.form_submit_button(
            label="Завершить",
            use_container_width=True,
            type="secondary",
            on_click=close_user_challenge,
            args=(user_challenge.id,),
        )


def render_challenges_page() -> None:
    challenge_service = get_container().challenge
    user_id = st.session_state.user_id

    _render_new_challenge_picker()

    with st.container():
        new_challenges = challenge_service.assignments(user_id, ChallengeStatus.NEW)
        for user_challenge in new_challenges:
            _render_challenge_form(user_challenge, is_new=True)

        with st.container():
            for user_challenge in challenge_service.assignments(user_id, ChallengeStatus.ONGOING):
                _render_challenge_form(user_challenge, is_new=False)

        # Promote the just-displayed "new" challenges to "ongoing" after rendering them.
        challenge_service.activate_new([uc.id for uc in new_challenges if uc.id is not None])
