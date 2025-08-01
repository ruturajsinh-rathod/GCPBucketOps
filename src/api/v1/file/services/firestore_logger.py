from datetime import datetime, timezone
from typing import Literal

from google.cloud import firestore

from src.api.v1.file.enums import FileStatusEnum


class FirestoreLogger:
    def __init__(self):
        self.client = firestore.Client()
        self.collection_name = "file_audit_logs"

    async def log_event(
        self,
        event_type: FileStatusEnum,
        file_name: str,
        status: Literal["SUCCESS", "FAILURE"],
        metadata: dict = {},
    ):
        doc = {
            "event_type": event_type,
            "file_name": file_name,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }
        self.client.collection(self.collection_name).add(doc)
