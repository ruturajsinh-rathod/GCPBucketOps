from datetime import datetime
from uuid import UUID

from src.api.v1.file.enums import ContentTypeEnum, FileStatusEnum
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


class DownloadURLResponse(CamelCaseModel):
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


class BaseGCSData(CamelCaseModel):
    """
    Represents metadata for a single file (blob) stored in a Google Cloud Storage bucket.

    Attributes:
        name (str): The name (path/key) of the file in the bucket.
        size (int): The size of the file in bytes.
        updated (datetime): The last modified timestamp of the file.
        content_type (ContentTypeEnum): The MIME type of the file, such as 'application/pdf' or 'image/png'.
    """

    name: str
    size: int
    updated: datetime
    content_type: ContentTypeEnum


class GetAllGCSData(CamelCaseModel):
    """
    Represents a paginated response for files retrieved from a Google Cloud Storage bucket.

    Attributes:
        files (list[BaseGCSData]): A list of file metadata objects returned from GCS.
        next_page_token (str | None): A token to fetch the next page of results.
                                      This is `None` if there are no more pages.
    """

    files: list[BaseGCSData]
    next_page_token: str | None = None


class UploadURLResponse(CamelCaseModel):
    """
    Response model containing a signed URL for uploading a file to Google Cloud Storage.

    Attributes:
    - upload_url (str): A V4-signed URL that allows the client to upload a file directly
      to the GCS bucket using an HTTP PUT request.
    - valid_for_seconds (int): The number of seconds the signed URL remains valid
      before it expires.

    Usage:
    This model is typically returned by the `signed_upload_url` endpoint and used
    by clients to perform secure, temporary uploads without needing backend file handling.
    """

    upload_url: str
    valid_for_seconds: int


class ExpiredFileResponse(CamelCaseModel):
    """
    Represents a single expired file entry.

    Attributes:
        id (UUID): Unique identifier of the expired file.
        file_name (str): Name of the expired file.
    """

    id: UUID
    file_name: str


class ExpiredFilesResponse(CamelCaseModel):
    """
    Response schema containing a list of expired files.

    Attributes:
        expired_files (list[ExpiredFileResponse]): A list of expired file entries with minimal metadata.
    """

    expired_files: list[ExpiredFileResponse]
