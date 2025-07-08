SOMETHING_WENT_WRONG = "Something went wrong!"

SUCCESS = "SUCCESS"

INVALID_TOKEN = "Invalid Token!"

EXPIRED_TOKEN = "Expired Token!"

ERROR = "Error"

INVALID_CRED = "Invalid credentials"

UNAUTHORIZEDACCESS = "You are not authorized to perform this action."

GCS_FILE_EXISTS = (
    "The file already exists in Google Cloud Storage. "
    "Please use a different name or remove the existing file from storage."
)

DB_FILE_EXISTS = (
    "A file record with this name already exists in the database."
    " Please use a different name or remove the existing record."
)

GCS_FILE_NOT_FOUND = (
    "The file does not exist in Google Cloud Storage. "
    "It may have been deleted or the name or content type is incorrect."
)

DB_FILE_NOT_FOUND = "The file record does not exist in the database. It may have been removed or never created."

GCS_UPLOAD_EXCEPTION = "Failed to upload file. Please try again later."

GCS_REMOVE_EXCEPTION = "Failed to delete file. Please try again later."

GENERATE_URL_EXCEPTION = "Failed to generate pre-signed url. Please try again later."

GCS_DATA_FETCH_EXCEPTION = "Failed to retrieve data from Google Cloud Storage. Please try again later."
