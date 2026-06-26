"""
Local file storage backend for uploads.

Files are saved to the `uploads/` directory at the project root and
served statically by FastAPI at /uploads/<filename>.
"""

import os
import shutil
from uuid import uuid4
from fastapi import UploadFile


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def upload_file(file: UploadFile, folder: str = "") -> dict:
    """
    Save an uploaded file to the local uploads directory.
    Returns: {"url": str, "filename": str, "content_type": str}
    """
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid4()}{ext}"

    target_dir = os.path.join(UPLOAD_DIR, folder) if folder else UPLOAD_DIR
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


def download_bytes(file_path: str) -> bytes:
    """Read a file from the uploads directory by its relative path."""
    # Accept both "/uploads/foo.mp4" and "foo.mp4"
    clean = file_path.lstrip("/")
    if clean.startswith("uploads/"):
        clean = clean[len("uploads/"):]
    full_path = os.path.join(UPLOAD_DIR, clean)
    with open(full_path, "rb") as f:
        return f.read()
