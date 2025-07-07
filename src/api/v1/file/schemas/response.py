from datetime import datetime
from uuid import UUID

from src.api.v1.file.enums import FileStatusEnum
from src.core.utils import CamelCaseModel


class FileResponse(CamelCaseModel):
    """
        Response model representing a file stored in GCS and tracked in the database.

        Attributes:
            id (UUID): Unique identifier for the file.
            file_name (str): Name of the file as stored in GCS.
            gcs_uri (str): Full GCS URI of the file (e.g., gs://bucket_name/file_name).
            bucket_name (str): Name of the GCS bucket containing the file.
            size (int): Size of the file in bytes.
            content_type (str): MIME type of the file (e.g., image/jpeg, application/pdf).
            created_at (datetime): Timestamp when the file record was created.
            expires_at (datetime): Timestamp when the file is considered expired.
            deleted_at (datetime): Timestamp when the file was soft-deleted (null if active).
            status (FileStatusEnum): Current status of the file (e.g., uploaded, deleted).

        Notes:
            - This model is typically returned after uploading or retrieving file details.
            - Fields like `public_url` or `version` can be included later if needed.
        """

    id: UUID
    file_name: str
    gcs_uri: str
    bucket_name: str
    size: int
    content_type: str
    created_at: datetime
    expires_at: datetime
    deleted_at: datetime
    status: FileStatusEnum


class GenerateURLResponse(CamelCaseModel):
    """
        Response model for a pre-signed download URL for a file stored in GCS.

        Attributes:
            download_url (str): The pre-signed URL that allows temporary file download.
            valid_for_seconds (int): The number of seconds the signed URL remains valid.

        Notes:
            - This URL is generated on-demand and grants temporary, secure access to a private file.
        """
    download_url: str
    valid_for_seconds: int
