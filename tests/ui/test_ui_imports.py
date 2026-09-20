"""Import smoke test: every UI module must import cleanly on the installed Streamlit.

Streamlit decorators such as ``@st.dialog`` run at import time, so a removed API breaks the
whole app before the login form renders (this is how ``st.experimental_dialog`` did).
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import m8_team.ui


def _ui_modules() -> list[str]:
    return sorted(
        info.name
        for info in pkgutil.walk_packages(m8_team.ui.__path__, prefix="m8_team.ui.")
        if not info.ispkg
    )


@pytest.mark.parametrize("module_name", _ui_modules())
def test_ui_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)
