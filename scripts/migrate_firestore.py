"""Copy Firestore documents from one GCP project to another via the client SDK.

One-off, local-only migration tool for projects on the free Spark tier, where
Cloud Storage export/import and Cloud Functions aren't available. Reads every
document from the source project, writes a local JSON backup, then writes the
same documents (same collection, same document ID) into the target project.

Example:
    uv run python scripts/migrate_firestore.py \\
        --source-cred src/credentials/m8-team-stg-firebase.json \\
        --target-cred src/credentials/m8-team-target-firebase.json \\
        --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.cloud import firestore

logger = logging.getLogger("migrate_firestore")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(_handler)

DEFAULT_COLLECTIONS = [
    "users",
    "rewards",
    "challenges",
    "user_challenge",
    "user_bonus",
    "user_reward",
    "credentials",
]
FIRESTORE_BATCH_LIMIT = 500
DEFAULT_BATCH_SIZE = 400


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--source-cred",
        required=True,
        type=Path,
        help="Service account JSON key for the source project",
    )
    parser.add_argument(
        "--target-cred",
        required=True,
        type=Path,
        help="Service account JSON key for the target project",
    )
    parser.add_argument(
        "--target-project-id",
        default=None,
        help="Override the target project ID inferred from --target-cred",
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        default=list(DEFAULT_COLLECTIONS),
        help="Collections to migrate (default: all known collections)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scripts/backups"),
        help="Where to write the local JSON backup before writing to the target",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Documents per batch commit (max {FIRESTORE_BATCH_LIMIT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read the source and write a local backup only; skip writing to the target",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip read/write; only compare document counts between source and target",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the interactive confirmation prompt"
    )
    args = parser.parse_args(argv)
    if args.batch_size > FIRESTORE_BATCH_LIMIT:
        parser.error(
            f"--batch-size must be <= {FIRESTORE_BATCH_LIMIT} (Firestore's per-commit limit)"
        )
    return args


def make_client(cred_path: Path, project_id: str | None) -> firestore.Client:
    if not cred_path.is_file():
        raise SystemExit(f"Credential file not found: {cred_path}")
    kwargs: dict[str, Any] = {}
    if project_id:
        kwargs["project"] = project_id
    client: firestore.Client = firestore.Client.from_service_account_json(  # type: ignore[no-untyped-call]
        str(cred_path), **kwargs
    )
    logger.info(f"Connected to project '{client.project}' using {cred_path}")
    return client


def read_collection(client: firestore.Client, name: str) -> list[dict[str, Any]]:
    docs = [{"_id": doc.id, **(doc.to_dict() or {})} for doc in client.collection(name).stream()]
    logger.info(f"Read {len(docs)} document(s) from '{name}' in project '{client.project}'")
    return docs


def dump_backup(
    data: dict[str, list[dict[str, Any]]], output_dir: Path, source_project: str
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = output_dir / f"firestore-backup-{source_project}-{timestamp}.json"
    # default=str is intentional: this file is a human-readable audit artifact
    # only, never read back to drive writes, so lossy stringification of
    # Firestore Timestamp/GeoPoint values here is fine.
    with backup_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, default=str, ensure_ascii=False, indent=2)
    return backup_path


def chunked(items: list[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def write_collection(
    client: firestore.Client, name: str, docs: list[dict[str, Any]], batch_size: int
) -> int:
    written = 0
    for chunk in chunked(docs, batch_size):
        batch = client.batch()
        for doc in chunk:
            doc_id: str = doc["_id"]
            payload = {k: v for k, v in doc.items() if k != "_id"}
            batch.set(client.collection(name).document(doc_id), payload)
        batch.commit()
        written += len(chunk)
        logger.info(
            f"  committed {written}/{len(docs)} doc(s) to '{name}' in project '{client.project}'"
        )
    return written


def collection_count(client: firestore.Client, name: str) -> int:
    return sum(1 for _ in client.collection(name).stream())


def verify_counts(
    source: firestore.Client, target: firestore.Client, collections: list[str]
) -> bool:
    all_match = True
    logger.info(f"{'collection':<20}{'source':>10}{'target':>10}   match")
    for name in collections:
        source_count = collection_count(source, name)
        target_count = collection_count(target, name)
        match = source_count == target_count
        all_match = all_match and match
        logger.info(
            f"{name:<20}{source_count:>10}{target_count:>10}   {'OK' if match else 'MISMATCH'}"
        )
    return all_match


def confirm_or_exit(
    source: firestore.Client, target: firestore.Client, collections: list[str], skip_prompt: bool
) -> None:
    if source.project == target.project:
        raise SystemExit(
            f"Source and target both resolve to project '{source.project}' - "
            "aborting to avoid overwriting data with itself."
        )
    print(f"About to migrate {len(collections)} collection(s): {', '.join(collections)}")
    print(f"  source: {source.project}")
    print(f"  target: {target.project}")
    if skip_prompt:
        return
    answer = input("Type 'yes' to continue: ")
    if answer.strip().lower() != "yes":
        raise SystemExit("Aborted.")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source = make_client(args.source_cred, None)
    target = make_client(args.target_cred, args.target_project_id)

    if args.verify_only:
        verify_counts(source, target, args.collections)
        return

    confirm_or_exit(source, target, args.collections, args.yes)

    data: dict[str, list[dict[str, Any]]] = {}
    for name in args.collections:
        data[name] = read_collection(source, name)

    backup_path = dump_backup(data, args.output_dir, source.project)
    logger.info(f"Local backup written to {backup_path}")

    if args.dry_run:
        logger.info("--dry-run: skipping writes to target project")
        return

    for name in args.collections:
        write_collection(target, name, data[name], args.batch_size)

    verify_counts(source, target, args.collections)
    logger.info("Done. Spot-check a few documents in the Firebase console before cutting over.")


if __name__ == "__main__":
    main()
