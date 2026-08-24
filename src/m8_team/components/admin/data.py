"""Data-access layer for the admin page.

Every Firestore read used across the admin tabs goes through this module. Collections that
back a whole tab's listing (challenges, rewards, user_challenge, the employee map) are cached
in `st.session_state` and only re-fetched when a mutation explicitly asks for it via
`force_refresh=True` - this replaces the ad-hoc `if "x" not in st.session_state` checks that
used to be scattered through show_admin_page().
"""

import logging
from datetime import date

import pandas as pd
import streamlit as st

from m8_team.components.firebase import (
    get_collection,
    get_earned_bonus_in_range,
    get_users,
    get_value,
)

from .constants import (
    CHALLENGES_COLLECTION,
    EXCLUDED_FROM_EMPLOYEE_LIST,
    REWARDS_COLLECTION,
    USER_CHALLENGE_COLLECTION,
    USERS_COLLECTION,
)

logger = logging.getLogger(__name__)


def get_user_bonus(selected_user_id: str) -> int | None:
    user_bonus = get_value(
        collection_name=USERS_COLLECTION,
        document_name=selected_user_id,
        field_name="user_free_bonuses",
    )
    if isinstance(user_bonus, int):
        return user_bonus
    if isinstance(user_bonus, str):
        try:
            return int(user_bonus)
        except Exception as e:
            logger.error(f"Couldn't convert 'user_bonus' to int. Error message: {e}")
            return None
    logger.error(f"'user_bonus' has unsupported type {type(user_bonus)}")
    return None


def _fetch_users_map() -> dict[str, str]:
    user_map: dict[str, str] = {}
    for key, value in get_users().items():
        if key not in EXCLUDED_FROM_EMPLOYEE_LIST:
            user_map[value["user_name"]] = key
    return user_map


def get_users_map(*, force_refresh: bool = False) -> dict[str, str]:
    if force_refresh or "users_data_map" not in st.session_state:
        st.session_state.users_data_map = _fetch_users_map()
    return st.session_state.users_data_map  # type: ignore[no-any-return]


def _fetch_challenges_df() -> pd.DataFrame:
    challenges = get_collection(collection_name=CHALLENGES_COLLECTION)
    for challenge in challenges:
        challenge["challenge_date_update"] = str(challenge["challenge_date_update"])
    return pd.DataFrame(challenges)


def get_challenges_df(*, force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or "challenge_df" not in st.session_state:
        st.session_state.challenge_df = _fetch_challenges_df()
    return st.session_state.challenge_df


def _fetch_rewards_df() -> pd.DataFrame:
    return pd.DataFrame(get_collection(collection_name=REWARDS_COLLECTION))


def get_rewards_df(*, force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or "rewards_df" not in st.session_state:
        st.session_state.rewards_df = _fetch_rewards_df()
    return st.session_state.rewards_df


def _fetch_user_challenge_df() -> pd.DataFrame:
    return pd.DataFrame(get_collection(collection_name=USER_CHALLENGE_COLLECTION))


def get_user_challenge_df(*, force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or "user_challenge_df" not in st.session_state:
        st.session_state.user_challenge_df = _fetch_user_challenge_df()
    return st.session_state.user_challenge_df


def _fetch_earned_bonus_df(start: date, end: date) -> pd.DataFrame:
    docs = get_earned_bonus_in_range(start=start, end=end)
    records = []
    for doc in docs:
        doc_data = doc.to_dict()
        if doc_data is None:
            continue
        records.append({**doc_data, "id": doc.id})
    return pd.DataFrame(records)


def get_earned_bonus_df(start: date, end: date, *, force_refresh: bool = False) -> pd.DataFrame:
    """ "charge bonus" transactions for [start, end], re-fetched whenever the range changes -
    the query is already scoped server-side (see get_earned_bonus_in_range), so there's no
    whole-collection cache to keep fresh here the way the other get_x_df functions have."""
    range_key = (start, end)
    if force_refresh or st.session_state.get("earned_bonus_range_key") != range_key:
        st.session_state.earned_bonus_df = _fetch_earned_bonus_df(start, end)
        st.session_state.earned_bonus_range_key = range_key
    return st.session_state.earned_bonus_df
