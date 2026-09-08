# show all commands
default:
    just --list

# install dependecies
install: && _init_precommit
    uv sync

# start app
run:
    APP_ENV=dev uv run streamlit run src/m8_team/app.py

# lint (fast check)
check:
    uv run ruff check .

# formatting
format:
    uv run ruff format .

# type checking
typecheck:
    uv run mypy .

# full link
lint: check typecheck

# (lint + format)
fix: format check typecheck

test:
    uv run pytest

_init_precommit:
    uv run pre-commit install
