from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status

from src.api.v1.file.enums import ContentTypeEnum
from src.api.v1.file.schemas import DownloadURLResponse, FileResponse
from src.api.v1.file.schemas.response import GetAllGCSData, UploadURLResponse
from src.api.v1.file.services import FileService
from src.core.basic_auth import basic_auth
from src.core.utils.schema import BaseResponse

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="upload",
    description="Upload file",
    operation_id="upload_file",
)
async def upload(
    _: Annotated[bool, Depends(basic_auth)],
    file: Annotated[UploadFile, File(...)],
    service: Annotated[FileService, Depends()],
) -> BaseResponse[FileResponse]:
    """
    Upload a file to GCS and store metadata in the database.
    """
    return BaseResponse(
        data=await service.upload(file=file),
        code=status.HTTP_201_CREATED,
    )


@router.delete(
    "/{file_name}",
    status_code=status.HTTP_200_OK,
    name="delete",
    description="Delete file",
    operation_id="delete_file",
)
async def delete(
    _: Annotated[bool, Depends(basic_auth)],
    file_name: Annotated[str, Path()],
    content_type: Annotated[ContentTypeEnum, Query()],
    service: Annotated[FileService, Depends()],
) -> BaseResponse:
    """
    Delete a file from GCS and mark it as deleted in the database.
    """
    return BaseResponse(
        data=await service.delete(file_name=file_name, content_type=content_type),
        code=status.HTTP_200_OK,
    )


@router.get(
    "/{file_name}/download-url",
    status_code=status.HTTP_200_OK,
    name="generate url",
    description="Generate url",
    operation_id="generate_url",
)
async def generate_url(
    _: Annotated[bool, Depends(basic_auth)],
    file_name: Annotated[str, Path()],
    content_type: Annotated[ContentTypeEnum, Query()],
    service: Annotated[FileService, Depends()],
) -> BaseResponse[DownloadURLResponse]:
    """
    Generate a pre-signed download URL for a file in GCS.
    """
    return BaseResponse(
        data=await service.generate_url(file_name=file_name, content_type=content_type),
        code=status.HTTP_200_OK,
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="get all",
    description="Get all",
    operation_id="get_all",
)
async def get_all(
    _: Annotated[bool, Depends(basic_auth)],
    service: Annotated[FileService, Depends()],
    page_token: Annotated[str | None, Query()] = None,
    max_results: Annotated[int | None, Query(ge=1)] = 100,
) -> BaseResponse[GetAllGCSData]:
    """
    Retrieve a paginated list of all files from the GCS bucket.

    This endpoint returns metadata for files stored in the Google Cloud Storage (GCS) bucket.
    It supports pagination using a page token and allows limiting the number of results per page.

    Authorization:
        Requires basic authentication.

    Query Parameters:
        page_token (str | None): A token indicating the start of the page of results. Optional.
        max_results (int | None): Maximum number of results to return (minimum 1, default is 100).

    Returns:
        BaseResponse[GetAllGCSData]: A structured response containing the list of files
        and pagination metadata.
    """

    return BaseResponse(
        data=await service.get_all(page_token=page_token, max_results=max_results),
        code=status.HTTP_200_OK,
    )


@router.get(
    "/signed-upload-url",
    status_code=status.HTTP_200_OK,
    name="signed upload url",
    description="Signed upload url",
    operation_id="signed_upload_url",
)
async def upload_url(
    _: Annotated[bool, Depends(basic_auth)],
    file_name: Annotated[str, Query()],
    content_type: Annotated[ContentTypeEnum, Query()],
    service: Annotated[FileService, Depends()],
) -> BaseResponse[UploadURLResponse]:
    """
    Returns a signed URL for securely uploading a file to Google Cloud Storage.

    This endpoint provides a time-limited signed URL that allows authenticated users to
    upload a file directly to GCS via an HTTP PUT request. The client must specify the
    target file name and content type to ensure the upload is accepted by the signed URL.

    Parameters:
    - file_name (str): The name (including optional path) of the file to be uploaded to GCS.
    - content_type (ContentTypeEnum): The MIME type of the file to be uploaded (e.g., 'image/png', 'application/pdf').

    Returns:
    - A structured response containing:
        - `upload_url`: The signed PUT URL for direct upload to GCS.
        - `expires_at`: The UTC timestamp when the signed URL will expire.

    Authentication:
    - Requires valid basic authentication credentials.

    Usage:
    - The client must upload the file using an HTTP PUT request and match the exact `Content-Type`.
    - If the file is large or needs resumability, consider using a resumable signed URL flow.
    """
    return BaseResponse(
        data=await service.signed_upload_url(file_name=file_name, content_type=content_type),
        code=status.HTTP_200_OK,
    )
