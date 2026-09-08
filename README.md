# m8_team

An internal app for a small marketing company, used to increase employee involvement.
Employees complete useful challenges, earn internal bonuses, and spend them ordering rewards.

## Quick start

```sh
uv sync
just run
```

Requires a `.env` (or environment) with at least:

- `APP_ENV` — `dev` / `stg` / `prod`
- `T_BOT_ENDPOINT` — notification bot endpoint
- Firebase service account credentials under `src/credentials/` (see [Setup](#setup))

## Setup

After cloning, run once to enable git hooks:

```sh
pre-commit install
```

(this also runs automatically via `just install`)

## Development

Common tasks are defined in the [justfile](justfile):

```sh
just install    # uv sync + install pre-commit hooks
just run        # start the app locally
just check      # lint (ruff)
just format     # format (ruff)
just typecheck  # mypy
just lint       # check + typecheck
just fix        # format + check + typecheck
just test       # pytest
```

## Project layout

```
src/m8_team/app.py     Streamlit entrypoint
src/m8_team/backend/   transport-agnostic: domain, repositories, services, notifications
                       (no streamlit imports)
src/m8_team/ui/        Streamlit UI: admin + user pages, calls backend/services
src/credentials/       Firebase service account keys (gitignored)
scripts/               one-off admin scripts, not part of the app/CI (see scripts/README.md)
tests/                 backend/{domain,services,repositories} + architecture guard
DEPLOYMENT.md          deployment pipeline & one-time server setup
```

The dependency rule: `ui/` imports `backend/`, never the reverse; nothing under `backend/`
imports `streamlit`. `tests/architecture/test_layering.py` enforces it.

## Deployment

The app runs as a Docker container, built and deployed via GitHub Actions to a Timeweb VPS,
with separate NOP (staging) and PROD environments. See [DEPLOYMENT.md](DEPLOYMENT.md) for details.
