import asyncio
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from google.cloud import storage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import db_session, get_session
from src.api import FileModel
from src.api.v1.file.enums import FileStatusEnum
from src.core.gcs import BUCKET_NAME, SERVICE_ACCOUNT_FILE
from src.core.utils import background_logger


class Scheduler:

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize the UserService with a database session.

        Args:
            session (AsyncSession): An asynchronous SQLAlchemy session injected via dependency.
        """
        self.session = session

    async def delete_old_files(self) -> None:
        """
        Deletes expired files from Google Cloud Storage (GCS) and marks them as deleted in the database.

        This method performs the following steps:
        - Queries the database for files where `expires_at` is in the past and `deleted_at` is null.
        - Iterates over the list of expired files.
        - Deletes each corresponding file from the configured GCS bucket.

        Any exceptions during the deletion process are logged using the background logger.

        Returns:
            None
        """

        try:
            client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
            bucket = client.bucket(BUCKET_NAME)

            files = await self.session.scalars(
                select(FileModel.file_name).where(
                    FileModel.expires_at
                    < datetime.now(timezone.utc).replace(tzinfo=None),
                    FileModel.deleted_at.is_(None),
                )
            )

            files = files.all()

            for file in files:
                blob = bucket.blob(file)
                if blob.exists():
                    blob.delete()
                else:
                    background_logger.warning(
                        f"{file} is not found in GCS but exists in our db."
                    )
                file.status = FileStatusEnum.DELETED
                file.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)

            return
        except Exception as exc:
            background_logger.error(
                f"An error occurred when deleting expired files from GCS: {exc}"
            )


async def periodic_cleanup():
    """
    Runs delete_old_files after every 24 hours
    """
    while True:
        try:
            async with get_session() as session:
                scheduler = Scheduler(session=session)

                await scheduler.delete_old_files()

        except Exception as exc:
            background_logger.error(f"Error occurred in periodic cleanup: {exc}")

        await asyncio.sleep(60 * 60 * 24)  # 1 day
