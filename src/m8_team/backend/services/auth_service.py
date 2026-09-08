"""Auth config load / registration persistence. Ported from ``firebase.get_credentials``
and ``firebase.register_user``.
"""

from __future__ import annotations

from typing import Any

from m8_team.backend.repositories.credentials_repo import CredentialsRepo


class AuthService:
    def __init__(self, credentials: CredentialsRepo) -> None:
        self._credentials = credentials

    def load_config(self) -> dict[str, Any]:
        return self._credentials.load()

    def persist_registration(self, config: dict[str, Any]) -> bool:
        return self._credentials.save(config)
