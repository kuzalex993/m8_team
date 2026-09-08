"""Lazy, memoized Firestore client.

Unlike the old ``components/firebase.py`` this does **no** work at import time - the client
is created on first ``get_client()`` call. That removes the need for the import-time
monkeypatching in ``tests/unit/conftest.py`` for anything above the repository layer.
"""

from __future__ import annotations

from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from m8_team.backend.config import Config

_APP_NAME = "firebase_connector"
_client: Any = None


def get_client(config: Config) -> Any:
    """Return a process-wide singleton Firestore client for ``config``."""
    global _client
    if _client is not None:
        return _client

    try:
        app = firebase_admin.get_app(_APP_NAME)
    except ValueError:
        cred = credentials.Certificate(str(config.firebase_cred_path))
        app = firebase_admin.initialize_app(cred, name=_APP_NAME)

    _client = firestore.client(app)
    return _client


def reset_client() -> None:
    """Test hook: drop the cached client so the next ``get_client`` rebuilds it."""
    global _client
    _client = None
