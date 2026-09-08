"""``credentials`` collection - the streamlit-authenticator config, one document per section."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseRepo
from .collections import CREDENTIALS

logger = logging.getLogger(__name__)


class CredentialsRepo(BaseRepo):
    def load(self) -> dict[str, Any]:
        logger.info("Getting credentials")
        docs = self._db.collection(CREDENTIALS).stream()
        return {doc.id: doc.to_dict() for doc in docs}

    def save(self, config: dict[str, Any]) -> bool:
        try:
            for key, value in config.items():
                self._db.collection(CREDENTIALS).document(key).update(value)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Error: %s", exc)
            return False
