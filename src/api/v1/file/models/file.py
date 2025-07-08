import uuid
from datetime import datetime, timedelta, timezone
from typing import Self
from uuid import UUID

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import func, text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base
from src.api.v1.file.enums import FileStatusEnum


class FileModel(Base):
    """
    SQLAlchemy model representing a file stored in Google Cloud Storage (GCS) and tracked in the database.

    Attributes:
        id (UUID): Primary key, unique identifier for the file.
        file_name (str): Name of the file as stored in GCS.
        gcs_uri (str): Full GCS URI of the file (e.g., gs://bucket_name/file_name).
        bucket_name (str): Name of the GCS bucket where the file is stored.
        size (int, optional): Size of the file in bytes.
        content_type (str, optional): MIME type of the file (e.g., image/jpeg, application/pdf).
        public_url (str, optional): Public URL of the file if made accessible.
        version (str, optional): Application-specific version of the file.
        created_at (datetime): Timestamp when the file record was created.
        expires_at (datetime, optional): Timestamp when the file is considered expired.
        deleted_at (datetime, optional): Timestamp when the file was soft-deleted (null if active).
        status (FileStatusEnum): Status of the file (e.g., uploaded, processing, deleted).

    Notes:
        - The `expires_at` field is set to 7 days after creation by default via the `create` method.
        - The `deleted_at` field implements soft deletion for the file.
    """

    __tablename__ = "files"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(nullable=False)
    gcs_uri: Mapped[str] = mapped_column(nullable=False)
    bucket_name: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[int] = mapped_column(nullable=True)
    content_type: Mapped[str] = mapped_column(nullable=True)
    public_url: Mapped[str] = mapped_column(nullable=True)
    version: Mapped[str] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(server_default=text("(NOW() + INTERVAL '7 days')"), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    status: Mapped[FileStatusEnum] = mapped_column(SqlEnum(FileStatusEnum, name="filestatusenum"), nullable=False)

    @classmethod
    def create(
        cls,
        file_name: str,
        gcs_uri: str,
        bucket_name: str,
        status: FileStatusEnum,
        size: int | None = None,
        content_type: str | None = None,
        public_url: str | None = None,
        version: str | None = None,
    ) -> Self:
        """
        Factory method to create a new FileModel instance with default values.

        Args:
            file_name (str): Name of the file as stored in GCS.
            gcs_uri (str): Full GCS URI of the file.
            bucket_name (str): Name of the GCS bucket where the file resides.
            status (FileStatusEnum): Status of the file (e.g., uploaded, deleted).
            size (int, optional): Size of the file in bytes.
            content_type (str, optional): MIME type of the file.
            public_url (str, optional): Public URL of the file if made accessible.
            version (str, optional): Version of the file.

        Returns:
            Self: A new instance of FileModel ready to be added to the database.

        Notes:
            - Automatically generates a UUID for the file.
            - Sets `expires_at` to 7 days from the current UTC time.
        """

        return cls(
            id=uuid.uuid4(),
            file_name=file_name,
            gcs_uri=gcs_uri,
            bucket_name=bucket_name,
            status=status,
            size=size,
            content_type=content_type,
            public_url=public_url,
            version=version,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        )
