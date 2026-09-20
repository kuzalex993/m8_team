"""AST guard: source must not use Streamlit APIs that were removed or deprecated by 1.62.

- ``st.experimental_*`` were removed (e.g. ``experimental_dialog`` -> ``st.dialog``).
- ``use_container_width`` is deprecated in favour of ``width="stretch"`` / ``width="content"``
  and logs a warning on every rerun.
"""

from __future__ import annotations

import ast
import pathlib

_SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "m8_team"


def _violations() -> list[str]:
    bad: list[str] = []
    for path in sorted(_SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            where = f"{path.relative_to(_SRC)}:{getattr(node, 'lineno', '?')}"
            if isinstance(node, ast.keyword) and node.arg == "use_container_width":
                bad.append(f"{where}: use_container_width (use width=...)")
            elif isinstance(node, ast.Attribute) and node.attr.startswith("experimental_"):
                bad.append(f"{where}: st.{node.attr} (removed)")
    return bad


def test_no_removed_or_deprecated_streamlit_api() -> None:
    assert _violations() == []
