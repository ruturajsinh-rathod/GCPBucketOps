from enum import Enum


class FileStatusEnum(str, Enum):
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


class ContentType(str, Enum):
    """
    Enumeration of common MIME content types for files.

    This class categorizes MIME types into the following groups:
    - Images (e.g., JPEG, PNG, SVG)
    - Audio (e.g., MP3, WAV, AAC)
    - Video (e.g., MP4, WEBM, AVI)
    - Text (e.g., plain text, HTML, CSV)
    - Application (e.g., PDF, JSON, ZIP, Office documents)
    - Binary (e.g., octet-stream)

    Each enum member maps a human-readable name to its corresponding MIME type string.

    Methods:
        file_extension() -> str:
            Returns the typical file extension associated with the content type.

    Example:
        >>> ContentType.JSON.value
        'application/json'

        >>> ContentType.JSON.file_extension()
        '.json'
    """

    # Images
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    BMP = "image/bmp"
    SVG = "image/svg+xml"
    WEBP = "image/webp"
    TIFF = "image/tiff"

    # Audio
    MP3 = "audio/mpeg"
    WAV = "audio/wav"
    OGG = "audio/ogg"
    AAC = "audio/aac"
    FLAC = "audio/flac"

    # Video
    MP4 = "video/mp4"
    MPEG = "video/mpeg"
    OGG_VIDEO = "video/ogg"
    WEBM = "video/webm"
    AVI = "video/x-msvideo"

    # Text
    PLAIN = "text/plain"
    HTML = "text/html"
    CSS = "text/css"
    CSV = "text/csv"
    XML = "text/xml"
    JAVASCRIPT = "text/javascript"

    # Application
    JSON = "application/json"
    PDF = "application/pdf"
    ZIP = "application/zip"
    GZIP = "application/gzip"
    TAR = "application/x-tar"
    RAR = "application/vnd.rar"
    MSWORD = "application/msword"
    EXCEL = "application/vnd.ms-excel"
    POWERPOINT = "application/vnd.ms-powerpoint"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    # Binary
    OCTET_STREAM = "application/octet-stream"

    def file_extension(self) -> str:
        """
        Get the standard file extension associated with the MIME content type.

        Returns:
            str: The file extension (including the leading dot),
                 or an empty string if the MIME type is unrecognized.

        Example:
            >>> ContentType.MP3.file_extension()
            '.mp3'
        """

        mapping = {
            # Images
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/svg+xml": ".svg",
            "image/webp": ".webp",
            "image/tiff": ".tiff",
            # Audio
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg",
            "audio/aac": ".aac",
            "audio/flac": ".flac",
            # Video
            "video/mp4": ".mp4",
            "video/mpeg": ".mpeg",
            "video/ogg": ".ogv",
            "video/webm": ".webm",
            "video/x-msvideo": ".avi",
            # Text
            "text/plain": ".txt",
            "text/html": ".html",
            "text/css": ".css",
            "text/csv": ".csv",
            "text/xml": ".xml",
            "text/javascript": ".js",
            # Application
            "application/json": ".json",
            "application/pdf": ".pdf",
            "application/zip": ".zip",
            "application/gzip": ".gz",
            "application/x-tar": ".tar",
            "application/vnd.rar": ".rar",
            "application/msword": ".doc",
            "application/vnd.ms-excel": ".xls",
            "application/vnd.ms-powerpoint": ".ppt",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
            # Binary
            "application/octet-stream": ".bin",
        }

        return mapping.get(self.value, "")
