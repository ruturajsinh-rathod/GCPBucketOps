from google.cloud import storage

from config.config import gcs_settings
from src.core.utils import core_logger

SERVICE_ACCOUNT_FILE = gcs_settings.GOOGLE_APPLICATION_CREDENTIALS
BUCKET_NAME = gcs_settings.BUCKET_NAME

client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)


def upload_to_gcs(file_data, destination_blob_name):
    """
    Uploads a file to Google Cloud Storage.

    Args:
        file_data: A file-like object to upload (e.g., UploadFile.file).
        destination_blob_name (str): The desired path/name for the file in the GCS bucket.

    Returns:
        str: The GCS URI of the uploaded file (e.g., gs://bucket_name/file_name).

    Raises:
        Exception: Logs a critical error and propagates the exception if upload fails.
    """

    try:
        client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(file_data)
        core_logger.info(f"File uploaded to gs://{BUCKET_NAME}/{destination_blob_name}")
        return f"gs://{BUCKET_NAME}/{destination_blob_name}"
    except Exception as exc:
        core_logger.critical(f"Failed to upload file to GCS: {exc}")
