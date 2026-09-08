"""Transport-agnostic backend for m8_team.

Nothing under this package may import ``streamlit``. The Streamlit UI (``m8_team.ui``)
depends on ``m8_team.backend.services`` and ``m8_team.backend.domain`` only.
"""
