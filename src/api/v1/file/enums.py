import enum


class FileStatusEnum(str, enum.Enum):
    """
    Enum representing the possible statuses of a file in the system.

    Attributes:
        PENDING: The file is awaiting upload or processing.
        UPLOADED: The file has been successfully uploaded to the storage.
        EXPIRED: The file has passed its expiration date and is considered expired.
        DELETED: The file has been marked as deleted, either logically or physically removed.
    """

    PENDING = "PENDING"
    UPLOADED = "UPLOADED"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"
