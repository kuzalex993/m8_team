"""Single source of truth for the timestamp format used across Firestore documents.

Previously the literal ``"%Y-%m-%dT%H:%M:%S.%fZ"`` was retyped in ~15 places.
"""

from __future__ import annotations

from datetime import UTC, datetime

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"


def now_iso() -> str:
    """Current UTC time as the ISO-8601 string stored in ``date`` / ``*_date`` fields."""
    return datetime.now(UTC).strftime(ISO_FORMAT)


def today_str() -> str:
    return datetime.now(UTC).strftime(DATE_FORMAT)
