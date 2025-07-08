from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import gcs_settings
from database.db import db_session
from src.api.v1.file.enums import ContentTypeEnum, FileStatusEnum
from src.api.v1.file.exceptions import (
    DBFileDoesNotExistsException,
    DBFileExistsException,
    GCSDataFetchException,
    GCSFileDoesNotExistsException,
    GCSFileExistsException,
    GCSRemoveException,
    GCSUploadException,
    GenerateURLException,
)
from src.api.v1.file.models.file import FileModel
from src.api.v1.file.schemas import GenerateURLResponse
from src.api.v1.file.schemas.response import BaseGCSData, GetAllGCSData
from src.core.gcs import BUCKET_NAME, client, upload_to_gcs
from src.core.utils import core_logger


class FileService:
    """
    Service class for handling file operations with Google Cloud Storage (GCS) and the database.

    This service provides methods to:
    - Upload files to GCS and create a corresponding database record.
    - Delete files from GCS and mark them as deleted in the database.
    - Generate a signed download URL for a file stored in GCS.

    Attributes:
        session (AsyncSession): SQLAlchemy asynchronous session for database operations.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize the FileService with a database session.

        Args:
            session (AsyncSession): An asynchronous SQLAlchemy session injected via dependency.
        """
        self.session = session

    async def upload(self, file: UploadFile) -> FileModel:
        """
        Upload a file to GCS and create a corresponding record in the database.

        Steps:
        - Checks if the file already exists in GCS.
        - Checks if the file record already exists in the database.
        - Uploads the file to GCS.
        - Creates a database record for the file.

        Args:
            file (UploadFile): The file to be uploaded.

        Returns:
            FileModel: The created file record.

        Raises:
            GCSFileExistsException: If the file already exists in GCS.
            DBFileExistsException: If the file record already exists in the database.
            GCSUploadException: For any unexpected upload failures.
        """

        try:
            # Check if file exists in GCS
            if client.bucket(BUCKET_NAME).blob(file.filename).exists(client):
                core_logger.warning(f"File '{file.filename}' already exists in GCS.")
                raise GCSFileExistsException

            # Check if file record exists in DB
            file_obj = await self.session.scalar(
                select(FileModel).where(
                    FileModel.file_name == file.filename,
                    FileModel.deleted_at.is_(None),
                    FileModel.bucket_name == BUCKET_NAME,
                )
            )

            if file_obj:
                core_logger.warning(f"File record '{file.filename}' already exists in the database.")
                raise DBFileExistsException

            # Upload to GCS
            gcs_uri = upload_to_gcs(file.file, file.filename)
            core_logger.info(f"File '{file.filename}' uploaded to GCS at '{gcs_uri}'.")

            # Create DB record
            file_obj = FileModel.create(
                file_name=file.filename,
                gcs_uri=gcs_uri,
                bucket_name=BUCKET_NAME,
                status=FileStatusEnum.UPLOADED,
                size=file.size,
                content_type=file.content_type,
                version="0.0.1",
            )
            self.session.add(file_obj)
            core_logger.info(f"File record for '{file.filename}' created in database.")

            return file_obj

        except (GCSFileExistsException, DBFileExistsException):
            raise

        except Exception as exc:
            core_logger.critical(f"Unexpected error while uploading file '{file.filename}': {exc}")
            raise GCSUploadException

    async def delete(self, file_name: str, content_type: ContentTypeEnum) -> dict[str, str]:
        """
        Delete a file from GCS and mark it as deleted in the database.

        Steps:
        - Verifies the file exists in GCS.
        - Deletes the file from GCS.
        - Marks the corresponding file record as deleted in the database.

        Args:
            file_name (str): The name of the file to delete.

        Returns:
            dict[str, str]: Success message.

        Raises:
            GCSFileDoesNotExistsException: If the file does not exist in GCS.
            DBFileDoesNotExistsException: If the file record does not exist in the database.
            ServiceUnavailable: For unexpected failures during deletion.
        """

        try:
            file_name = f"{file_name}{content_type.file_extension()}"
            bucket = client.bucket(BUCKET_NAME)
            blob = bucket.blob(file_name)

            if not blob.exists():
                core_logger.warning(f"File '{file_name}' does not exist in GCS.")
                raise GCSFileDoesNotExistsException

            blob.delete()
            core_logger.info(f"File '{file_name}' deleted from GCS.")

            file = await self.session.scalar(
                select(FileModel).where(
                    FileModel.file_name == file_name,
                    FileModel.deleted_at.is_(None),
                    FileModel.bucket_name == BUCKET_NAME,
                )
            )

            if file:
                file.status = FileStatusEnum.DELETED
                file.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
                core_logger.info(f"File record for '{file_name}' marked as deleted in DB.")
            else:
                core_logger.warning(f"File record '{file_name}' does not exist in DB.")
                raise DBFileDoesNotExistsException

            return {"message": f"File '{file_name}' deleted successfully."}

        except (DBFileDoesNotExistsException, GCSFileDoesNotExistsException):
            raise

        except Exception as exc:
            core_logger.critical(f"Failed to remove file '{file_name}' from GCS or DB: {exc}")
            raise GCSRemoveException

    async def generate_url(self, file_name: str, content_type: ContentTypeEnum) -> GenerateURLResponse:
        """
        Generate a pre-signed, temporary download URL for a file stored in GCS.

        Args:
            file_name (str): The name of the file to generate the URL for.

        Returns:
            GenerateURLResponse: The generated signed URL and its validity duration.

        Raises:
            GCSFileDoesNotExistsException: If the file does not exist in GCS.
        """

        try:
            file_name = f"{file_name}{content_type.file_extension()}"
            bucket = client.bucket(BUCKET_NAME)

            blob = bucket.blob(file_name)

            if not blob.exists():
                raise GCSFileDoesNotExistsException

            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=gcs_settings.EXPIRATION_SECONDS),
                method="GET",
            )

            return GenerateURLResponse(download_url=url, valid_for_seconds=gcs_settings.EXPIRATION_SECONDS)

        except GCSFileDoesNotExistsException:
            raise

        except Exception as exc:
            core_logger.critical(f"Failed to generate url for '{file_name}': {exc}")
            raise GenerateURLException

    async def get_all(self, max_results: int, page_token: str | None = None) -> GetAllGCSData:
        """
        Retrieve a paginated list of files from the Google Cloud Storage (GCS) bucket.

        This method lists files (blobs) in the configured GCS bucket, starting from the
        given page token and returning up to the specified number of results. It also
        returns the `next_page_token` if more files are available.

        Args:
            page_token (str): A token indicating the page of results to fetch.
                              Use `None` or an empty string to start from the beginning.
            max_results (int): Maximum number of files to return in a single call.

        Returns:
            GetAllGCSData: An object containing:
                - `files`: A list of `BaseGCSData` entries for each file in the bucket.
                - `next_page_token`: A string token for fetching the next page of results,
                                     or `None` if there are no more results.

        Raises:
            GCSDataFetchException: If there is an error while accessing GCS.

        Logging:
            Logs a critical error if GCS data fetch fails.
        """
        try:
            bucket = client.get_bucket(BUCKET_NAME)

            blobs = bucket.list_blobs(page_token=page_token, max_results=max_results)

            file_list = []
            next_page_token = None

            for blob in blobs:
                file_list.append(
                    BaseGCSData(
                        name=blob.name,
                        size=blob.size,
                        updated=blob.updated,
                        content_type=blob.content_type,
                    )
                )

            if blobs.next_page_token:
                next_page_token = blobs.next_page_token

            return GetAllGCSData(files=file_list, next_page_token=next_page_token)

        except Exception as exc:
            core_logger.critical(f"Failed to fetch GCS data: {exc}")
            raise GCSDataFetchException
