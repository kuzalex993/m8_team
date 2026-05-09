import logging
import os
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_document import (
    DocumentSnapshot,
)
from google.cloud.firestore_v1.base_query import BaseCompositeFilter, FieldFilter
from google.cloud.firestore_v1.stream_generator import StreamGenerator

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(_handler)

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings:
    ENV = os.getenv("APP_ENV", "dev")

    FIREBASE_CRED_PATH = {
        "dev": BASE_DIR / "credentials" / "m8-team-dev-firebase.json",
        "stg": BASE_DIR / "credentials" / "m8-team-stg-firebase.json",
        "prod": BASE_DIR / "credentials" / "m8-team-prod-firebase.json",
    }[ENV]


try:
    app = firebase_admin.get_app("firebase_connector")
except ValueError:
    cred = credentials.Certificate(Settings.FIREBASE_CRED_PATH)
    app = firebase_admin.initialize_app(cred, name="firebase_connector")

db = firestore.client(app)


def get_credentials() -> dict[str, Any]:
    logger.info("Getting credentials")
    doc_ref = db.collection("credentials")
    docs = doc_ref.stream()
    res = dict()
    for doc in docs:
        res[doc.id] = doc.to_dict()
    return res


def register_user(config: dict[str, str]) -> bool:
    try:
        for key in config.keys():
            doc_ref = db.collection("credentials").document(key)
            doc_ref.update(config[key])
        return True
    except Exception as e:
        logger.error(f"Error:{e}")
        return False


def create_user(email: str, user: str, name: str) -> bool:
    data = {
        "user_email": email,
        "user_free_bonuses": 0,
        "user_name": name,
        "user_position": "сотрудник",
        "user_reserved_bonuses": 0,
        "user_role": "user",
        "chat_id": None,
    }
    try:
        collection_ref = db.collection("users")
        document_ref = collection_ref.document(user)
        document_ref.set(data)
        return True
    except Exception as e:
        logger.error(e)
        return False


def get_users() -> dict[str, Any]:
    logger.info("Retrieve users data")
    doc_ref = db.collection("users")
    docs = doc_ref.stream()
    res = dict()
    for doc in docs:
        res[doc.id] = doc.to_dict()
    return res


def update_value(collection: str, document: str, field: str, value: Any) -> bool:
    try:
        doc_ref = db.collection(collection).document(document)
        doc_ref.update({field: value})
        return True
    except Exception:
        return False


def get_collection(collection_name: str) -> list[dict[Any | str, Any]]:
    logger.info(f"Retrieve {collection_name} data")
    doc_ref = db.collection(collection_name)
    docs = doc_ref.stream()
    items = list(map(lambda x: {**x.to_dict(), "id": x.id}, docs))
    return items


def get_document(collection_name: str, document_name: str) -> dict[str, Any] | Any | None:
    logger.info(f"Retrieving data: collection - {collection_name}, document - {document_name}")
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        doc_data = doc.to_dict()
        return doc_data
    except Exception as e:
        logger.error(e)
        return None


def get_value(collection_name: str, document_name: str, field_name: str) -> Any:
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        doc_data = doc.to_dict()
        field_value = doc_data[field_name]
        return field_value
    except Exception as e:
        logger.error(e)
        return False


def add_new_document(collection_name: str, document_data: dict[str, Any]) -> Any | None:
    try:
        collection_ref = db.collection(collection_name)
        update_time, document_ref = collection_ref.add(document_data=document_data)
        logger.info(
            f"""{update_time} Added new document with id '{document_ref.id}'
            to collection '{collection_name}'"""
        )
        return document_ref.id
    except Exception as e:
        logger.error(f"Error: Couldn't add document to collection '{collection_name}'")
        logger.error(f"--- Error message: {e}")
        return None


def update_document(collection_name: str, document_id: str, document_data: dict[str, Any]) -> bool:
    try:
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.update(document_data)
        logger.info(f"Updated document '{document_id}' in collection '{collection_name}'")
        return True
    except Exception as e:
        logger.error(
            f"Error: Couldn't update  document '{document_id}' in collection '{collection_name}'"
        )
        logger.error(f"--- Error message: {e}")
        return False


def put_into_user_bonus_collection(
    user_id: str, transaction_type: str, bonus_value: int, event_type: str, event_id: int | None
) -> bool:
    new_record = {
        "user_id": user_id,
        "transaction_type": transaction_type,
        "bonus_value": bonus_value,
        "event_type": event_type,
        "event_id": event_id,
        "date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    if add_new_document("user_bonus", new_record) is not None:
        return True
    else:
        return False


def update_user_bonus_atomic(
    user_id: str,
    transaction_type: str,
    bonus_value: int,
    event_type: str,
    event_id: int | None,
) -> bool:
    try:
        new_bonus_ref = db.collection("user_bonus").document()
        user_ref = db.collection("users").document(user_id)
        new_record = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "bonus_value": bonus_value,
            "event_type": event_type,
            "event_id": event_id,
            "date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        batch = db.batch()
        batch.set(new_bonus_ref, new_record)
        batch.update(user_ref, {"user_free_bonuses": firestore.Increment(bonus_value)})
        batch.commit()
        logger.info(f"Atomic bonus update for user '{user_id}': delta={bonus_value}")
        return True
    except Exception as e:
        logger.error(f"Atomic bonus update failed for user '{user_id}': {e}")
        return False


def put_into_user_challenge_collection(
    user_id: int,
    user_name: str,
    challenge_id: int,
    challenge_descripion: str,
    start_date: date,
    challenge_duration: int,
    challenge_creation_date: str,
) -> bool:
    new_record = {
        "user_id": user_id,
        "user_name": user_name,
        "challenge_id": challenge_id,
        "challenge_descripion": challenge_descripion,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "planned_finish_date": (start_date + timedelta(days=challenge_duration)).strftime(
            "%Y-%m-%d"
        ),
        "fact_finish_date": None,
        "challenge_status": "new",
        "challenge_success": "uknonwn",
        "challenge_creation_date": challenge_creation_date,
    }
    if add_new_document("user_challenge", new_record) is not None:
        return True
    else:
        return False


def get_user_challenges(user_id: str, challenge_status: str) -> Iterator[DocumentSnapshot]:

    logger.info(f"Retrieving challenges of {user_id}")
    try:
        filter_list = [
            FieldFilter("user_id", "==", user_id),
            FieldFilter("challenge_status", "==", challenge_status),
        ]
        docs = cast(
            StreamGenerator[DocumentSnapshot],
            db.collection("user_challenge")
            .where(filter=BaseCompositeFilter("AND", filter_list))  # type: ignore[arg-type]
            .stream(),
        )
        return docs
    except Exception as e:
        logger.error(e)
        return iter([])


def get_user_rewards(user_id: str) -> Iterator[DocumentSnapshot]:
    logger.info(f"Retrieving rewards of {user_id}")
    if user_id != "all":
        try:
            filter_list = [FieldFilter("user_id", "==", user_id)]
            docs = cast(
                StreamGenerator[DocumentSnapshot],
                db.collection("user_reward")
                .where(filter=BaseCompositeFilter("AND", filter_list))  # type: ignore[arg-type]
                .stream(),
            )
            return docs
        except Exception as e:
            logger.error(e)
            return iter([])
    else:
        try:
            docs = cast(StreamGenerator[DocumentSnapshot], db.collection("user_reward").stream())
            return docs
        except Exception as e:
            logger.error(e)
            return iter([])
