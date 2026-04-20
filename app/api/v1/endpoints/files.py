"""
File proxy endpoint.

When STORAGE_BACKEND=azure, blob URLs require signed tokens (SAS) for access
because public access is disabled. This endpoint:
  1. Takes a blob filename
  2. Generates a fresh signed URL (valid for 4 hours)
  3. Redirects the browser to the signed URL

This endpoint is intentionally public (no auth required) because:
  - The SAS token on the Azure URL provides access control
  - HTML elements like <video> and <a> can't send Authorization headers
  - The signed URLs are time-limited (4 hours) and read-only
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{blob_name:path}", summary="Get a signed URL for a stored file")
def get_file(blob_name: str):
    """
    Generate a time-limited signed URL for the given blob and redirect to it.
    Works for videos, PDFs, docs, images — any file stored in Azure.
    """
    from app.core.storage import get_storage_backend, AzureBlobStorageBackend

    storage = get_storage_backend()

    if isinstance(storage, AzureBlobStorageBackend):
        signed_url = storage.get_signed_url(blob_name, expiry_hours=4)
        return RedirectResponse(url=signed_url, status_code=302)
    else:
        # Local storage — redirect to the local uploads path
        return RedirectResponse(url=f"/uploads/{blob_name}", status_code=302)
