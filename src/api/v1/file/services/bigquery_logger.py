from datetime import datetime, timezone
from typing import Literal

from google.cloud import bigquery

from src.api.v1.file.enums import FileStatusEnum


class BigQueryLogger:
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"

    async def log_event(
        self,
        event_type: FileStatusEnum,
        file_name: str,
        status: Literal["SUCCESS", "FAILURE"],
        metadata: dict = {},
    ):
        row = {
            "event_type": event_type,
            "file_name": file_name,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }
        errors = self.client.insert_rows_json(self.table_ref, [row])
        if errors:
            print("BigQuery insert error:", errors)
