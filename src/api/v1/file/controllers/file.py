from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile, status

from src.api.v1.file.schemas import FileResponse, GenerateURLResponse
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
    service: Annotated[FileService, Depends()],
) -> BaseResponse:
    """
    Delete a file from GCS and mark it as deleted in the database.
    """
    return BaseResponse(
        data=await service.delete(file_name=file_name),
        code=status.HTTP_200_OK,
    )


@router.post(
    "/generate-url/{file_name}",
    status_code=status.HTTP_200_OK,
    name="generate url",
    description="Generate url",
    operation_id="generate_url",
)
async def generate_url(
    _: Annotated[bool, Depends(basic_auth)],
    file_name: Annotated[str, Path()],
    service: Annotated[FileService, Depends()],
) -> BaseResponse[GenerateURLResponse]:
    """
    Generate a pre-signed download URL for a file in GCS.
    """
    return BaseResponse(
        data=await service.generate_url(file_name=file_name),
        code=status.HTTP_200_OK,
    )
