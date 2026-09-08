"""Static guard for the UI/backend split (see CLAUDE.md 'Layering rules').

Walks the source tree and asserts the import contract by inspecting each module's AST:

- nothing under ``m8_team.backend`` may import ``streamlit``
- nothing under ``m8_team.ui`` (or ``app.py``) may import ``firebase_admin`` /
  ``google.cloud`` / ``m8_team.backend.repositories`` / ``m8_team.backend.notifications``
- ``m8_team.backend.domain`` may not import any other ``m8_team`` layer, ``firebase_admin``,
  ``google.cloud``, ``streamlit`` or ``requests``
"""

from __future__ import annotations

import ast
import pathlib

_SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "m8_team"


def _imported_names(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def _modules(*relative: str) -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for rel in relative:
        target = _SRC / rel
        out.extend(target.rglob("*.py") if target.is_dir() else [target])
    return out


def _violations(paths: list[pathlib.Path], forbidden_prefixes: tuple[str, ...]) -> list[str]:
    bad: list[str] = []
    for path in paths:
        for name in _imported_names(path):
            if any(name == p or name.startswith(p + ".") for p in forbidden_prefixes):
                bad.append(f"{path.relative_to(_SRC)} imports {name}")
    return bad


def test_backend_never_imports_streamlit() -> None:
    assert _violations(_modules("backend"), ("streamlit",)) == []


def test_ui_never_imports_firestore_or_lower_backend_layers() -> None:
    forbidden = (
        "firebase_admin",
        "google.cloud",
        "m8_team.backend.repositories",
        "m8_team.backend.notifications",
    )
    assert _violations(_modules("ui", "app.py"), forbidden) == []


def test_domain_is_pure() -> None:
    forbidden = (
        "streamlit",
        "requests",
        "pandas",
        "firebase_admin",
        "google.cloud",
        "m8_team.backend.repositories",
        "m8_team.backend.services",
        "m8_team.backend.notifications",
        "m8_team.backend.container",
        "m8_team.ui",
    )
    assert _violations(_modules("backend/domain"), forbidden) == []
