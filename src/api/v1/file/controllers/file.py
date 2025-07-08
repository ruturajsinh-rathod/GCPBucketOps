from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status

from src.api.v1.file.enums import ContentTypeEnum
from src.api.v1.file.schemas import FileResponse, GenerateURLResponse
from src.api.v1.file.schemas.response import GetAllGCSData
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
) -> BaseResponse[GenerateURLResponse]:
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

    return BaseResponse(
        data=await service.get_all(page_token=page_token, max_results=max_results),
        code=status.HTTP_200_OK,
    )


@router.post(
    "/{file_name}/public",
    status_code=status.HTTP_200_OK,
    name="make public url",
    description="Make public url",
    operation_id="make_public_url",
    include_in_schema=False
)
async def public_url(
    _: Annotated[bool, Depends(basic_auth)],
    file_name: Annotated[str, Path()],
    content_type: Annotated[ContentTypeEnum, Query()],
    service: Annotated[FileService, Depends()],
) -> BaseResponse[GenerateURLResponse]:

    return BaseResponse(
        data=await service.make_public_url(file_name=file_name, content_type=content_type),
        code=status.HTTP_200_OK,
    )
