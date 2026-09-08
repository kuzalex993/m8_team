"""Runtime configuration, read from the environment exactly once.

Replaces the scattered ``os.getenv`` / ``load_dotenv`` calls that used to sit at module
level in ``firebase.py``, ``notifications.py`` and ``userPage.py``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# src/m8_team/backend/config.py -> src/
# The Firebase key lives under src/credentials/ (see entrypoint.sh, Dockerfile,
# DEPLOYMENT.md); it is *not* inside the m8_team package.
_SRC_ROOT = Path(__file__).resolve().parents[2]

_FIREBASE_CRED_FILENAMES = {
    "dev": "m8-team-dev-firebase.json",
    "stg": "m8-team-stg-firebase.json",
    "prod": "m8-team-prod-firebase.json",
}


@dataclass(frozen=True)
class Config:
    env: str
    firebase_cred_path: Path
    bot_token: str | None
    bot_endpoint: str | None

    @classmethod
    def from_env(cls) -> Config:
        load_dotenv()
        env = os.getenv("APP_ENV", "dev")
        cred_filename = _FIREBASE_CRED_FILENAMES.get(env, _FIREBASE_CRED_FILENAMES["dev"])
        return cls(
            env=env,
            firebase_cred_path=_SRC_ROOT / "credentials" / cred_filename,
            bot_token=os.getenv("BOT_TOKEN"),
            bot_endpoint=os.getenv("T_BOT_ENDPOINT"),
        )
