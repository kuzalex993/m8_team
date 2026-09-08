# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`m8_team` is an internal employee-engagement app for a small marketing company. Employees
take on "challenges" (tasks), earn internal bonus points, and spend them ordering rewards.
It is a single Streamlit UI backed entirely by Firebase Firestore — there is no other
database, ORM, or standalone backend service. UI-facing strings are in Russian.

## Commands

Tasks are defined in the [justfile](justfile) (wraps `uv`):

```sh
just install      # uv sync + install pre-commit hooks
just run          # APP_ENV=dev uv run streamlit run src/m8_team/app.py
just check        # ruff check .
just format       # ruff format .
just typecheck    # mypy .   (strict mode; CI runs `mypy src`)
just lint         # check + typecheck
just fix          # format + check + typecheck
just test         # pytest (with coverage, config in pyproject.toml)
```

Run a single test:

```sh
uv run pytest tests/backend/repositories/test_bonus_ledger_repo.py
uv run pytest tests/backend/repositories/test_bonus_ledger_repo.py::test_commit_failure_returns_false
uv run pytest -k atomic
```

CI (`.github/workflows/ci.yml`) runs `ruff check`, `mypy src`, and `pytest` on PRs to
`main` and pushes to `feature/**`. The pre-commit config blocks direct commits to `main`
(`no-commit-to-branch`), so work on a branch and open a PR.

## Architecture

The code is split into a **transport-agnostic backend package** and a **Streamlit UI
package**. The dependency rule is one-directional: `ui/` imports `backend/`, never the
reverse, and nothing under `backend/` imports `streamlit`. `tests/architecture/test_layering.py`
enforces this by AST-scanning the source on every `pytest` run.

```
src/m8_team/
  app.py                  Streamlit entrypoint (auth + admin/user routing)
  backend/
    config.py             Config dataclass, read once from env (APP_ENV, BOT_TOKEN, ...)
    container.py           build_container(): Config -> repositories -> services
    domain/               pure: models, enums, errors, rules, clock, results, constants
    repositories/         the ONLY importers of firebase_admin / google.cloud.firestore
    notifications/        Telegram client
    services/             use-cases the UI calls (auth, user, bonus, challenge, reward, stats)
  ui/
    container.py          get_container(): build once, cache in st.session_state
    auth.py               streamlit_authenticator wiring
    common/               cache.py (session_state read cache), feedback.py, labels.py
    admin/                page.py dispatcher + menu.py + state.py + crud.py + tabs/*.py
    user/                 page.py dispatcher + charts.py + pages/*.py
```

### Request flow

`src/m8_team/app.py` is the only Streamlit entrypoint. On every rerun it:

1. `ui/auth.py::load_users_config()` reads the auth config from the Firestore `credentials`
   collection (via `AuthService.load_config()`), caches it in
   `st.session_state["users_config"]`, and builds a `streamlit_authenticator` `Authenticate`.
2. Renders the login form. Registration calls `AuthService.persist_registration()` (writes
   the `credentials` collection back) and `UserService.create_employee()` (creates a `users`
   doc).
3. Routes by username: `user_id == "admin"` → `ui/admin/page.py::show_admin_page()`,
   everyone else → `ui/user/page.py::show_user_page()`.

Both pages use `streamlit_option_menu` sidebars and drive state through `st.session_state`.

### Backend layers

- **`backend/domain/`** — standard library only. `models.py` has the `@dataclass` mirrors of
  the Firestore docs (`User`, `Reward`, `Challenge`, `UserChallenge`, `UserBonus`,
  `UserReward`), each with `to_dict()` / `from_dict(d, doc_id=...)`. The Firestore field is
  misspelled `challenge_descripion`; that string is confined to `UserChallenge.from_dict` /
  `to_dict` and `UserChallengeRepo.assign` — everything above uses `description`. `enums.py`
  replaces the old magic strings (`TransactionType`, `EventType`, `ChallengeStatus`,
  `RewardStatus`); their values are the exact persisted strings. `clock.py` owns the ISO
  timestamp format. `rules.py` is pure predicates (`completed_on_time`, `can_afford`, ...).
- **`backend/repositories/`** — the low-level Firestore layer, the only place
  `firebase_admin` / `google.cloud.firestore` is imported. `firestore.py::get_client(config)`
  is lazy and memoized — no import-time Firebase init (this is why the tests need no global
  `firebase_admin` monkeypatch). `base.py::BaseRepo` holds the generic get/list/add/update
  helpers; one concrete repo per collection. `Config.env` reads `APP_ENV`
  (`dev`/`stg`/`prod`) and picks `src/credentials/m8-team-<env>-firebase.json` (gitignored);
  a missing key crashes on the first request, not at import.
- **`backend/services/`** — use-cases. They take plain arguments and return
  `domain/results.py` objects or raise `domain/errors.py` exceptions; they never touch
  Streamlit. The UI maps results/errors to `st.success` / `st.error` in
  `ui/common/feedback.py`.

### Firestore collections

`credentials` (auth config, one doc per section), `users` (doc id = username; holds
`user_free_bonuses`, `user_reserved_bonuses`, `chat_id`, ...), `challenges`, `rewards`,
`user_challenge`, `user_reward`, `user_bonus` (append-only transaction ledger).
Document IDs are used as foreign keys across collections (e.g. `user_bonus.user_id` is a
`users` doc id), so preserve IDs in any migration.

### Bonus economy

Each user has `user_free_bonuses` (spendable) and `user_reserved_bonuses` (locked against
a pending reward request). Every balance change also appends a `user_bonus` ledger row.
`transaction_type` values live in `domain/enums.py::TransactionType`
(`"charge bonus"`, `"write off bonus"`, `"reserve bonus"`, `"debiting bonus"`).

**All balance mutations go through `backend/repositories/bonus_ledger_repo.py`** — one of
`charge_atomic` (admin add / write-off, challenge reward), `reserve_atomic` (reward
request: free → reserved), or `settle_reserved_atomic` (admin confirms a reward). Each does
the ledger insert + balance delta in a single Firestore `batch` with `firestore.Increment`.
The older read-modify-write-in-Python pattern from the pre-split code is gone; do not
reintroduce it.

### Admin / user page structure

`ui/admin/page.py` is the dispatcher: `MENU_ITEMS` (in `ui/admin/menu.py`) + `_TAB_RENDERERS`
map labels to `render_*_tab()` functions — add a tab by extending both.
`ui/admin/state.py::ensure_session_state()` primes the `ui/common/cache.py` reads and widget
defaults once per session. `ui/admin/crud.py` holds the shared
expander→form→submit→toast flow for the "add / edit item" UIs in the Задания and Награды
tabs. `ui/user/page.py` dispatches the three user pages under `ui/user/pages/`.
`ui/common/cache.py` is the session-state read cache (whole-collection listings fetched once,
re-read only on `force_refresh=True` after a mutation) — the UI-side replacement for the old
`components/admin/data.py`.

Telegram notifications: `backend/notifications/telegram.py` (token from `Config.bot_token`,
env var `BOT_TOKEN`), fronted by `backend/services/notification_service.py` which resolves
each user's `chat_id` from the `users` doc.

## Deployment

Same Docker image for all environments; behavior is selected at runtime by `APP_ENV` in
the server-side env file plus a Firebase key mounted as a file at
`/app/src/credentials/m8-team-<env>-firebase.json`. `src/entrypoint.sh` optionally
materializes the key from `$FIREBASE_CREDENTIALS` before `exec`ing Streamlit on port 8080.

GitHub Actions build → push to `ghcr.io/<owner>/m8_team` → SSH deploy to a Timeweb VPS:

| Trigger | Env | Image tag | Container | Port |
|---|---|---|---|---|
| push to `main` | NOP / staging (`m8-team-stg`) | `:nop` | `m8-nop` | 8502 |
| push to `release/**` | PROD (`m8-team-prod`) | `:prod` | `m8-prod` | 8503 |

Full details and one-time server setup: [DEPLOYMENT.md](DEPLOYMENT.md).

## Tests

`pyproject.toml` sets `pythonpath = ["src"]`, so imports are `from m8_team... import ...`.
Layout under `tests/`:

- `tests/backend/domain/` — pure, no mocking.
- `tests/backend/services/` — repositories replaced with `MagicMock`s; no Firebase.
- `tests/backend/repositories/` — the Firestore client is a `MagicMock` passed into the
  repo constructor (see `test_bonus_ledger_repo.py`); still no `firebase_admin` patching
  because `get_client` is lazy.
- `tests/architecture/test_layering.py` — AST guard for the UI/backend import contract.

## Scripts

`scripts/migrate_firestore.py` copies data between two Firestore projects with the client
SDK (Spark-tier friendly). It stands up its own two `firestore.Client`s by credential path
(it is a two-project tool, so it does not use `backend/repositories/firestore.py`'s
single-project client). Not in the Docker image, not run by CI. See
[scripts/README.md](scripts/README.md); always `--dry-run` first (writes a PII backup
under `scripts/backups/`, gitignored).
