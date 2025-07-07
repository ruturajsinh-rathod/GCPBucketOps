from fastapi import status

from src import constants
from src.core.exceptions import (
    AlreadyExistsError,
    CustomException,
    NotFoundError,
    ServiceUnavailable,
    UnauthorizedError,
)


class InvalidCredsException(UnauthorizedError):
    """
    Raised when the provided login credentials are invalid.
    """

    message = constants.INVALID_CRED


class UnauthorizedAccessException(UnauthorizedError):
    """
    Raised when a file attempts to access a resource they are not authorized for.
    """

    message = constants.UNAUTHORIZEDACCESS


class GCSFileExistsException(AlreadyExistsError):
    message = constants.GCS_FILE_EXISTS


class DBFileExistsException(AlreadyExistsError):
    message = constants.DB_FILE_EXISTS


class GCSFileDoesNotExistsException(NotFoundError):
    message = constants.GCS_FILE_NOT_FOUND


class DBFileDoesNotExistsException(NotFoundError):
    message = constants.DB_FILE_NOT_FOUND


class GCSUploadException(ServiceUnavailable):
    message = constants.GCS_UPLOAD_EXCEPTION


class GCSRemoveException(ServiceUnavailable):
    message = constants.GCS_REMOVE_EXCEPTION


class GenerateURLException(ServiceUnavailable):
    message = constants.GENERATE_URL_EXCEPTION
