# Integration testing

Integration tests currently run **only locally, from a developer's computer**.
They can connect to a local Firestore emulator or the remote development database.
Running this suite in CI/CD, deployment workflows or on the application server is
not currently configured.

Run all commands from the repository root after `uv sync --group dev`.
The suite is `tests/integration/test_reward_resolution_firestore.py`.

## Scenarios

Five cases verify repeated cancellation, concurrent cancellations of one order,
confirmation racing cancellation, cancellation of two orders belonging to one user,
and an injected failure before commit. Assertions check both balances, final order
status, decision date, ledger amounts and owners, and absence of duplicate decisions.
Reservations link to orders through `user_bonus.event_id = user_reward document ID`;
the reservation document's own ID differs.

Fixtures seed orders and reservations directly. The suite tests order resolution;
it does not exercise the full order creation flow or audit existing database records.

## Local emulator

Install Google Cloud CLI and Java on PATH, then install the emulator:

```bash
gcloud components install cloud-firestore-emulator
```

For Homebrew OpenJDK on macOS, expose Java in the terminal starting the emulator:

```bash
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
java -version
```

Start the emulator in one terminal:

```bash
gcloud emulators firestore start --host-port=127.0.0.1:8085 --project=demo-reward-resolution
```

Run tests locally in a second terminal:

```bash
FIRESTORE_EMULATOR_HOST=127.0.0.1:8085 uv run pytest tests/integration/test_reward_resolution_firestore.py --no-cov -q
```

The fixture uses anonymous credentials and project `demo-reward-resolution`.
No Firebase key is needed. Stop the emulator with Ctrl+C after testing.

## Local run against the development database

The test process still runs on the developer's computer. This mode writes synthetic
documents to the remote dev database. Use a local development service-account key
with read/write/delete access to `users`, `user_reward` and `user_bonus`.
Keep credentials outside version control; never use production credentials.

```bash
unset FIRESTORE_EMULATOR_HOST
REWARD_TEST_PROJECT='<dev-project-id>' \
REWARD_TEST_CREDENTIALS=src/credentials/m8-team-dev-firebase.json \
uv run pytest tests/integration/test_reward_resolution_firestore.py --no-cov -q
```

Replace `<dev-project-id>` with the actual dev project ID. The fixture requires
that it match the key's project ID and contain `dev`. `APP_ENV` does not select the
database for this suite. If set, `FIRESTORE_EMULATOR_HOST` takes precedence.

## Data and cleanup

Each test creates a unique `reward-cancel-test-<uuid>-*` user, two orders and their
reservation entries. Initial balances are 20 free and 200 reserved bonuses; each
order reserves 100. Teardown removes only these synthetic documents and their linked
ledger records, leaving existing employees untouched.

Forced termination or cleanup failure can leave test documents behind. Identify the
exact UUID for the interrupted run before removing its documents and linked ledger
rows. Never delete entire collections or every document sharing the common prefix.

The reservation lookup needs the default single-field index on `event_id`.
Check index exemptions if the database reports a missing index.

## Ordinary tests and results

Without integration environment variables, `just test` skips the five cases.
CI currently runs ordinary tests without configuring the integration suite.
To run ordinary tests locally without an external database:

```bash
unset FIRESTORE_EMULATOR_HOST REWARD_TEST_PROJECT REWARD_TEST_CREDENTIALS
just test
```

Record emulator and dev results separately: date, command, pass/fail/skip counts and
cleanup outcome. An unavailable dev database remains an incomplete check even if the
emulator tests pass. Do not include credentials or personal data in reports.

Concurrent decisions may encounter lock conflicts. The repository retries aborted
transactions with jitter, up to five attempts. Persistent errors are test failures;
do not ignore them or infer that an error message alone proves no commit occurred.
