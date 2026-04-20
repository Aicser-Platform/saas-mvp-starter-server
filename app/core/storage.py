"""
Storage backend abstraction for file uploads.

Supports two backends:
  - local: saves to the local `uploads/` directory (default, for dev)
  - azure: uploads to Azure Blob Storage with signed-URL support

Selected via env var:  STORAGE_BACKEND=local|azure

Azure env vars (required when STORAGE_BACKEND=azure):
  - AZURE_STORAGE_CONNECTION_STRING
  - AZURE_STORAGE_CONTAINER  (default: "uploads")
"""

import os
import shutil
from abc import ABC, abstractmethod
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()


class StorageBackend(ABC):
    """Abstract file storage interface."""

    @abstractmethod
    async def upload(self, file: UploadFile, folder: str = "") -> dict:
        """
        Upload a file and return metadata:
          {"url": str, "filename": str, "content_type": str}
        """
        ...

    @abstractmethod
    def get_signed_url(self, file_path: str, expiry_hours: int = 4) -> str:
        """Return a time-limited signed URL for a stored file."""
        ...


# ── Local Storage (dev/default) ──────────────────────────────────────────────

class LocalStorageBackend(StorageBackend):
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def upload(self, file: UploadFile, folder: str = "") -> dict:
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid4()}{ext}"

        target_dir = os.path.join(self.upload_dir, folder) if folder else self.upload_dir
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_path = f"/uploads/{folder}/{unique_filename}" if folder else f"/uploads/{unique_filename}"
        return {
            "url": relative_path,
            "filename": unique_filename,
            "content_type": file.content_type,
        }

    def get_signed_url(self, file_path: str, expiry_hours: int = 4) -> str:
        # Local storage doesn't need signed URLs — just return the path
        return file_path


# ── Azure Blob Storage ───────────────────────────────────────────────────────

class AzureBlobStorageBackend(StorageBackend):
    """
    Azure Blob Storage backend with SAS token signed URLs.
    Requires:
      pip install azure-storage-blob
    """

    def __init__(self, connection_string: str, container_name: str = "uploads"):
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise ImportError(
                "azure-storage-blob is required for Azure storage backend. "
                "Install it with: pip install azure-storage-blob"
            )

        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Create container if not exists
        container_client = self.blob_service_client.get_container_client(container_name)
        try:
            container_client.get_container_properties()
        except Exception:
            container_client.create_container()

    async def upload(self, file: UploadFile, folder: str = "") -> dict:
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid4()}{ext}"
        blob_name = f"{folder}/{unique_filename}" if folder else unique_filename

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name,
        )

        from azure.storage.blob import ContentSettings

        # Map content types explicitly for tricky formats
        content_type = file.content_type or "application/octet-stream"
        # Browsers sometimes send wrong MIME types for certain files
        ext_content_types = {
            ".mov": "video/quicktime",
            ".wmv": "video/x-ms-wmv",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".ogg": "video/ogg",
            ".pdf": "application/pdf",
        }
        if ext.lower() in ext_content_types:
            content_type = ext_content_types[ext.lower()]

        data = await file.read()
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(
                content_type=content_type,
                content_disposition="inline",  # render in browser, don't force download
            ),
        )

        # Return the blob URL (unsigned — use get_signed_url() for access)
        url = blob_client.url
        return {
            "url": url,
            "filename": unique_filename,
            "content_type": file.content_type,
            "blob_name": blob_name,
        }

    def get_signed_url(self, blob_name: str, expiry_hours: int = 4) -> str:
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions

        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name,
        )
        return f"{blob_client.url}?{sas_token}"


# ── Factory ──────────────────────────────────────────────────────────────────

_backend_instance: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    """
    Returns the configured storage backend singleton.
    Set STORAGE_BACKEND=azure to use Azure Blob Storage.
    """
    global _backend_instance
    if _backend_instance is not None:
        return _backend_instance

    backend_type = os.environ.get("STORAGE_BACKEND", "local").lower()

    if backend_type == "azure":
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.environ.get("AZURE_STORAGE_CONTAINER", "uploads")
        if not connection_string:
            raise ValueError(
                "AZURE_STORAGE_CONNECTION_STRING env var is required when STORAGE_BACKEND=azure"
            )
        _backend_instance = AzureBlobStorageBackend(connection_string, container_name)
    else:
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
        _backend_instance = LocalStorageBackend(upload_dir)

    return _backend_instance
