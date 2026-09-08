"""Aggregate views for the admin 'Статистика' tab. Pandas aggregation is fine here - the
return values are data, not control flow. Ported from ``components/admin/stats_tab.py``.

The aggregation methods take already-fetched rows so the UI can cache the reads (the old
``components/admin/data.py`` cached the ``user_bonus`` range query in ``session_state``);
``earned_bonus_rows`` is the thin fetch the UI cache wraps.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from m8_team.backend.domain.constants import EXCLUDED_EMPLOYEE_IDS
from m8_team.backend.domain.enums import ChallengeStatus
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo
from m8_team.backend.repositories.user_challenge_repo import UserChallengeRepo

from .user_service import UserService

SUCCESS_COLUMN = "Успешно"
FAILURE_COLUMN = "Неуспешно"


class StatsService:
    def __init__(
        self,
        user_challenges: UserChallengeRepo,
        ledger: BonusLedgerRepo,
        users: UserService,
    ) -> None:
        self._user_challenges = user_challenges
        self._ledger = ledger
        self._users = users

    def earned_bonus_rows(self, start: date, end: date) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for doc in self._ledger.earned_in_range(start, end):
            data = doc.to_dict()
            if data is None:
                continue
            rows.append({**data, "id": doc.id})
        return rows

    def finished_challenges_by_user(self, user_challenge_df: pd.DataFrame) -> pd.DataFrame:
        if user_challenge_df.empty:
            return pd.DataFrame()

        finished = user_challenge_df[
            (user_challenge_df["challenge_status"] == ChallengeStatus.FINISHED)
            & (~user_challenge_df["user_id"].isin(EXCLUDED_EMPLOYEE_IDS))
        ]
        if finished.empty:
            return pd.DataFrame()

        finished = finished.copy()
        finished[SUCCESS_COLUMN] = finished["challenge_success"] == True  # noqa: E712

        counts = (
            finished.groupby(["user_name", SUCCESS_COLUMN])
            .size()
            .unstack(fill_value=0)
            .rename(columns={True: SUCCESS_COLUMN, False: FAILURE_COLUMN})
            .reindex(columns=[SUCCESS_COLUMN, FAILURE_COLUMN], fill_value=0)
        )
        counts["_total"] = counts.sum(axis=1)
        return counts.sort_values("_total", ascending=False).drop(columns="_total")

    def bonuses_earned_by_user(self, earned_bonus_rows: list[dict[str, Any]]) -> pd.Series:
        df = pd.DataFrame(earned_bonus_rows)
        if df.empty:
            return pd.Series(dtype="int64")

        earned = df[~df["user_id"].isin(EXCLUDED_EMPLOYEE_IDS)]
        if earned.empty:
            return pd.Series(dtype="int64")

        id_to_name = {uid: name for name, uid in self._users.employee_map().items()}
        totals = earned.groupby("user_id")["bonus_value"].sum()
        totals.index = totals.index.map(lambda uid: id_to_name.get(uid, uid))
        totals.index.name = "user_name"
        return totals.sort_values(ascending=False)
