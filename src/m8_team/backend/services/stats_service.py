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
from m8_team.backend.domain.enums import ChallengeStatus, EventType
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo
from m8_team.backend.repositories.user_challenge_repo import UserChallengeRepo

from .user_service import UserService

SUCCESS_COLUMN = "Успешно"
FAILURE_COLUMN = "Неуспешно"

# Sources of earned bonuses, keyed by the ``event_type`` of the ``user_bonus`` ledger row.
# Rows with any other ``event_type`` are shown as OTHER_SOURCE_COLUMN (only when present)
# rather than silently dropped, so the stacked totals always add up.
CHALLENGE_SOURCE_COLUMN = "За задания"
ADMIN_SOURCE_COLUMN = "Начислено администратором"
OTHER_SOURCE_COLUMN = "Другое"
_SOURCE_COLUMNS = {
    EventType.USER_CHALLENGE: CHALLENGE_SOURCE_COLUMN,
    EventType.ADMIN: ADMIN_SOURCE_COLUMN,
}


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

    def _counted_mask(self, user_ids: pd.Series, include_inactive: bool) -> pd.Series:
        """Which rows count towards the stats, by ``user_id``.

        By default only current team members count: the ``users`` doc exists and is
        active. Everyone else is a former employee - including ids that only survive in
        ``user_challenge`` / ``user_bonus`` because their ``users`` doc was deleted.
        With ``include_inactive`` former employees are counted too; service accounts
        (``EXCLUDED_EMPLOYEE_IDS``) never are.
        """
        counted = ~user_ids.isin(EXCLUDED_EMPLOYEE_IDS)
        if include_inactive:
            return counted
        active_ids = {uid for _, uid, active in self._users.employee_directory() if active}
        return counted & user_ids.isin(active_ids)

    def earned_bonus_rows(self, start: date, end: date) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for doc in self._ledger.earned_in_range(start, end):
            data = doc.to_dict()
            if data is None:
                continue
            rows.append({**data, "id": doc.id})
        return rows

    def finished_challenges_by_user(
        self, user_challenge_df: pd.DataFrame, *, include_inactive: bool = False
    ) -> pd.DataFrame:
        if user_challenge_df.empty:
            return pd.DataFrame()

        finished = user_challenge_df[
            (user_challenge_df["challenge_status"] == ChallengeStatus.FINISHED)
            & self._counted_mask(user_challenge_df["user_id"], include_inactive)
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

    def bonuses_earned_by_user(
        self, earned_bonus_rows: list[dict[str, Any]], *, include_inactive: bool = False
    ) -> pd.DataFrame:
        """Earned bonuses per employee, one column per source (see ``_SOURCE_COLUMNS``),
        biggest earners first."""
        df = pd.DataFrame(earned_bonus_rows)
        if df.empty:
            return pd.DataFrame()

        earned = df[self._counted_mask(df["user_id"], include_inactive)]
        if earned.empty:
            return pd.DataFrame()

        source = earned["event_type"].map(_SOURCE_COLUMNS).fillna(OTHER_SOURCE_COLUMN)
        totals = (
            earned.groupby(["user_id", source])["bonus_value"]
            .sum()
            .unstack(fill_value=0)
            .reindex(columns=[CHALLENGE_SOURCE_COLUMN, ADMIN_SOURCE_COLUMN, OTHER_SOURCE_COLUMN])
        )
        totals = totals.fillna(0).astype("int64")
        if not totals[OTHER_SOURCE_COLUMN].any():
            totals = totals.drop(columns=OTHER_SOURCE_COLUMN)

        id_to_name = {uid: name for name, uid in self._users.employee_map().items()}
        totals.index = totals.index.map(lambda uid: id_to_name.get(uid, uid))
        totals.index.name = "user_name"
        return totals.loc[totals.sum(axis=1).sort_values(ascending=False).index]
