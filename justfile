# show all commands
default:
    just --list

# install dependecies
install:
    uv sync

# start app
run:
    uv run streamlit run src/m8_team/main.py

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