from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, UploadFile
from google.cloud import storage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

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
from src.api.v1.file.schemas import (
    BaseGCSData,
    DownloadURLResponse,
    ExpiredFilesResponse,
    GetAllGCSData,
    UploadURLResponse,
)
from src.api.v1.file.services.firestore_logger import FirestoreLogger
from src.core.gcs import BUCKET_NAME, client, upload_to_gcs
from src.core.utils import core_logger


def get_firestore_logger() -> FirestoreLogger:
    return FirestoreLogger()


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

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        firestore_logger: Annotated[FirestoreLogger, Depends(get_firestore_logger)],
    ) -> None:
        """
        Initialize the FileService with a database session.

        Args:
            session (AsyncSession): An asynchronous SQLAlchemy session injected via dependency.
        """
        self.session = session
        self.firestore_logger = firestore_logger

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

            await self.firestore_logger.log_event(
                event_type="UPLOAD",
                file_name=file.filename,
                status="SUCCESS",
                metadata={"content_type": file.content_type, "size": file.size},
            )

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

    async def generate_url(self, file_name: str, content_type: ContentTypeEnum) -> DownloadURLResponse:
        """
        Generate a pre-signed, temporary download URL for a file stored in GCS.

        Args:
            file_name (str): The name of the file to generate the URL for.

        Returns:
            DownloadURLResponse: The generated signed URL and its validity duration.

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

            return DownloadURLResponse(download_url=url, valid_for_seconds=gcs_settings.EXPIRATION_SECONDS)

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

    async def signed_upload_url(self, file_name: str, content_type: ContentTypeEnum) -> UploadURLResponse:
        """
        Generates a V4 signed URL for uploading a file to Google Cloud Storage.

        This method creates a signed URL using the HTTP PUT method, allowing clients to upload
        a file directly to the configured GCS bucket without passing through the backend.
        The signed URL is time-limited and requires the specified content type to match
        during the upload request.

        Parameters:
        - file_name (str): The name (and optional path) of the file to be uploaded.
        - content_type (ContentTypeEnum): The MIME type of the file (e.g., 'image/jpeg', 'application/pdf').

        Returns:
        - UploadURLResponse: An object containing the signed upload URL and its validity duration in seconds.

        Notes:
        - The client must use HTTP PUT with the exact `Content-Type` when uploading the file.
        - The signed URL will expire after the number of seconds defined in `gcs_settings.EXPIRATION_SECONDS`.
        """

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=gcs_settings.EXPIRATION_SECONDS),
            method="PUT",
            content_type=content_type.value,
        )

        return UploadURLResponse(upload_url=url, valid_for_seconds=gcs_settings.EXPIRATION_SECONDS)

    async def get_all_expired(self) -> ExpiredFilesResponse:
        """
        Retrieve all files that are expired and not yet marked as deleted.

        A file is considered expired if its `expires_at` timestamp is earlier than the current UTC time.
        This method excludes any files that have already been soft-deleted (i.e., have a non-null `deleted_at`).

        Returns:
            ExpiredFilesResponse: A response model containing the list of expired files with limited fields (id and file_name).
        """
        files = await self.session.scalars(
            select(FileModel)
            .options(load_only(FileModel.id, FileModel.file_name))
            .where(
                FileModel.expires_at < datetime.now(timezone.utc).replace(tzinfo=None),
                FileModel.deleted_at.is_(None),
            )
        )
        expired_files = files.all()

        await self.remove_all_expired([file.id for file in expired_files])

        return ExpiredFilesResponse(expired_files=expired_files)

    async def remove_all_expired(self, expired_files: list) -> dict:
        """
        Soft-delete the specified expired files by updating their status and deletion timestamp.

        Args:
            expired_files (list): A list of UUIDs corresponding to expired file records to be marked as deleted.

        This method updates each matched file by:
            - Setting its status to `FileStatusEnum.DELETED`
            - Assigning the current UTC timestamp to `deleted_at`

        Returns:
            dict: A simple dictionary containing a success message.
        """
        files = await self.session.scalars(select(FileModel).where(FileModel.id.in_(expired_files)))

        files = files.all()

        for file in files:
            file.status = FileStatusEnum.DELETED
            file.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)

        return {"message": "All expired files are deleted successfully!"}
