"""The real ``app.py`` script must start and show the login form for an anonymous visitor."""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from unittest.mock import MagicMock

from streamlit.testing.v1 import AppTest

_APP = str(pathlib.Path(__file__).resolve().parents[2] / "src" / "m8_team" / "app.py")

_USERS_CONFIG = {
    "credentials": {"usernames": {}},
    "cookie": {"name": "m8_test", "key": "secret", "expiry_days": 1},
}


def test_app_renders_login_form(make_app: Callable[..., AppTest], container: MagicMock) -> None:
    container.auth.load_config.return_value = _USERS_CONFIG

    at = make_app(_APP).run()

    assert not at.exception
    assert [b.label for b in at.button if b.label == "Войти"] == ["Войти"]
    assert {t.label for t in at.text_input} >= {"Имя пользователя", "Пароль"}
