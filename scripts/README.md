# scripts/

One-off admin scripts. Not deployed (excluded from the Docker image, which
only copies `src/` and `.streamlit/`) and not part of the app/CI.

## migrate_firestore.py

Copies data between two Firestore projects using the client SDK directly.
Meant for the free (Spark) tier, where Cloud Storage export/import and
Cloud Functions aren't available.

Migrates the known collections (`users`, `rewards`, `challenges`,
`user_challenge`, `user_bonus`, `user_reward`, `credentials`) by default,
preserving original document IDs (other collections reference them as
foreign keys, e.g. `user_bonus.user_id` -> a `users` document ID).

### Usage

1. Place the target project's service account key somewhere under
   `src/credentials/` (e.g. `src/credentials/m8-team-target-firebase.json`)
   - already gitignored.
2. Dry run first — reads the source and writes a local JSON backup under
   `scripts/backups/` (gitignored, contains PII) without touching the
   target:

   ```
   uv run python scripts/migrate_firestore.py \
     --source-cred src/credentials/m8-team-stg-firebase.json \
     --target-cred src/credentials/m8-team-target-firebase.json \
     --dry-run
   ```

3. Inspect the generated backup file, then run for real (drop `--dry-run`):

   ```
   uv run python scripts/migrate_firestore.py \
     --source-cred src/credentials/m8-team-stg-firebase.json \
     --target-cred src/credentials/m8-team-target-firebase.json
   ```

   Confirm the source/target prompt, or pass `--yes` to skip it.

4. The script prints a per-collection count comparison after writing. To
   re-check counts later without touching data: add `--verify-only`.
5. Writes are idempotent (upsert by document ID), so a failed or partial run
   can be safely re-run, optionally scoped with
   `--collections user_bonus user_reward`.

Run `uv run python scripts/migrate_firestore.py --help` for all flags.
