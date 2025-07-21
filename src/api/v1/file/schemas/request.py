from uuid import UUID

from pydantic import BaseModel


class RemoveExpiredFileRequest(BaseModel):
    """
    Request schema for removing expired files.

    Attributes:
        expired_files (list[UUID]): A list of UUIDs representing the IDs of expired files
                                    that should be marked as deleted.
    """

    expired_files: list[UUID]
