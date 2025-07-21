import os

import httpx
from google.cloud import storage

EXPIRED_FILE_API_URL = os.environ.get("EXPIRED_FILE_API_URL")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
AUTH_HEADER = os.environ.get("AUTH_HEADER")
DELETE_FILE_API_URL = os.environ.get("DELETE_FILE_API_URL")


def fetch_expired_files() -> list[str]:
    headers = {"accept": "application/json", "Authorization": AUTH_HEADER}
    response = httpx.get(EXPIRED_FILE_API_URL, timeout=10.0, headers=headers)
    response.raise_for_status()
    return response.json().get("data").get("expiredFiles")


def delete_from_database(expired_files: list) -> dict:
    headers = {"accept": "application/json", "Authorization": AUTH_HEADER}
    payload = {"expired_files": expired_files}
    response = httpx.post(DELETE_FILE_API_URL, json=payload, timeout=10.0, headers=headers)
    response.raise_for_status()
    return response.json().get("data")


def delete_from_gcs(filenames: list[str]) -> tuple[list[str], list[str]]:
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    deleted, missing = [], []

    for file_name in filenames:
        blob = bucket.blob(file_name)
        if blob.exists():
            blob.delete()
            deleted.append(file_name)
        else:
            missing.append(file_name)

    return deleted, missing


def delete_expired_files(request):
    try:

        expired_files = fetch_expired_files()
        expired_files = {"id": [d["id"] for d in expired_files], "fileName": [d["fileName"] for d in expired_files]}
        if not expired_files:
            return {"message": "No expired files to delete."}, 200

        deleted, missing = delete_from_gcs(expired_files.get("fileName"))
        delete_from_database(expired_files.get("id"))

        response = {
            "status": "success",
            "deleted_files": deleted,
            "not_found_files": missing,
            "total_deleted": len(deleted),
        }
        print(response)
        return response, 200

    except Exception as e:
        return {"error": str(e)}, 500
