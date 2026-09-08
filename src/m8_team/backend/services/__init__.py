"""Use-case layer. The Streamlit UI calls these and nothing below them.

Services take plain arguments, return ``m8_team.backend.domain.results`` objects, and raise
``m8_team.backend.domain.errors`` on expected failures. They never import ``streamlit``.
"""
