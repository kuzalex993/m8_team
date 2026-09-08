"""Generic Firestore helpers shared by the concrete repositories.

These are the lightly-reworked bodies of the generic functions that used to live in
``components/firebase.py`` (``get_collection``, ``get_document``, ``get_value``,
``add_new_document``, ``update_document``, ``update_value``).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any, cast

from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import BaseCompositeFilter, FieldFilter
from google.cloud.firestore_v1.stream_generator import StreamGenerator

logger = logging.getLogger(__name__)


class BaseRepo:
    def __init__(self, client: Any) -> None:
        self._db: Any = client

    # --- reads ---------------------------------------------------------------

    def list_collection(self, collection: str) -> list[dict[str, Any]]:
        logger.info("Retrieve %s data", collection)
        docs = self._db.collection(collection).stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]

    def get_document(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        try:
            doc = self._db.collection(collection).document(doc_id).get()
            data: dict[str, Any] | None = doc.to_dict()
            return data
        except Exception as exc:  # noqa: BLE001 - mirror old behaviour, log & degrade
            logger.error(exc)
            return None

    def get_value(self, collection: str, doc_id: str, field: str) -> Any:
        try:
            doc = self._db.collection(collection).document(doc_id).get()
            data = doc.to_dict()
            return data[field]
        except Exception as exc:  # noqa: BLE001
            logger.error(exc)
            return False

    def stream_where(
        self, collection: str, filters: list[FieldFilter]
    ) -> Iterator[DocumentSnapshot]:
        try:
            return cast(
                "StreamGenerator[DocumentSnapshot]",
                self._db.collection(collection)
                .where(filter=BaseCompositeFilter("AND", filters))  # type: ignore[arg-type]
                .stream(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(exc)
            return iter([])

    def stream_all(self, collection: str) -> Iterator[DocumentSnapshot]:
        try:
            return cast(
                "StreamGenerator[DocumentSnapshot]", self._db.collection(collection).stream()
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(exc)
            return iter([])

    # --- writes ------------------------------------------------------------

    def add_document(self, collection: str, data: dict[str, Any]) -> str | None:
        try:
            _update_time, ref = self._db.collection(collection).add(document_data=data)
            logger.info("Added document '%s' to '%s'", ref.id, collection)
            return str(ref.id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Couldn't add document to '%s': %s", collection, exc)
            return None

    def update_document(self, collection: str, doc_id: str, data: dict[str, Any]) -> bool:
        try:
            self._db.collection(collection).document(doc_id).update(data)
            logger.info("Updated document '%s' in '%s'", doc_id, collection)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Couldn't update '%s' in '%s': %s", doc_id, collection, exc)
            return False

    def update_value(self, collection: str, doc_id: str, field: str, value: Any) -> bool:
        return self.update_document(collection, doc_id, {field: value})

    def set_document(self, collection: str, doc_id: str, data: dict[str, Any]) -> bool:
        try:
            self._db.collection(collection).document(doc_id).set(data)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Couldn't set '%s' in '%s': %s", doc_id, collection, exc)
            return False
