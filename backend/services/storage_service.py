"""
SwachhLoop AI — Storage Service (Image Upload Abstraction)
=============================================================
Provides a clean interface for storing uploaded images.

Current implementation: local filesystem (uploads/ directory)
Future implementations: AWS S3, Google Cloud Storage, Supabase Storage

All consumers call save_upload() and receive a URL string.
They never know which backend is in use.

Phase 4+: Swap LocalStorageBackend for S3StorageBackend by changing
STORAGE_BACKEND in the .env file.
"""

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from backend.core.config import settings


# ---------------------------------------------------------------------------
# Abstract interface — DO NOT change the method signatures
# ---------------------------------------------------------------------------

class StorageBackend(ABC):
    """Interface for image/file storage providers."""

    @abstractmethod
    async def save(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """
        Persist file_bytes and return a publicly accessible URL.

        Args:
            file_bytes:   Raw file content.
            filename:     Original filename (used for extension only).
            content_type: MIME type (e.g. "image/jpeg").

        Returns:
            URL string pointing to the stored file.
        """

    @abstractmethod
    async def delete(self, url: str) -> None:
        """Remove the file identified by url."""


# ---------------------------------------------------------------------------
# Local filesystem implementation
# ---------------------------------------------------------------------------

class LocalStorageBackend(StorageBackend):
    """
    Stores files in the local uploads/ directory.
    Suitable for development only.
    In production, use a cloud storage backend.
    """

    def __init__(self, upload_dir: str = "uploads") -> None:
        self._dir = Path(upload_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        ext = Path(filename).suffix or ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest = self._dir / unique_name
        dest.write_bytes(file_bytes)
        # Return a relative URL that FastAPI can serve via StaticFiles
        return f"/uploads/{unique_name}"

    async def delete(self, url: str) -> None:
        filename = url.split("/")[-1]
        target = self._dir / filename
        if target.exists():
            target.unlink()


# ---------------------------------------------------------------------------
# Future S3 backend placeholder (Phase 4+)
# ---------------------------------------------------------------------------

class S3StorageBackend(StorageBackend):
    """
    AWS S3 / Supabase Storage backend.
    Phase 4+: implement using boto3 or supabase-py.
    """

    async def save(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        raise NotImplementedError(
            "S3StorageBackend is not yet implemented. Scheduled for Phase 4."
        )

    async def delete(self, url: str) -> None:
        raise NotImplementedError(
            "S3StorageBackend.delete() is not yet implemented. Scheduled for Phase 4."
        )


# ---------------------------------------------------------------------------
# Factory — returns the configured backend
# ---------------------------------------------------------------------------

def get_storage_backend() -> StorageBackend:
    """
    Return the active storage backend based on STORAGE_BACKEND env var.
    Defaults to local.
    """
    backend = settings.storage_backend.lower()
    if backend == "s3":
        return S3StorageBackend()
    return LocalStorageBackend(upload_dir=settings.upload_dir)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
storage = get_storage_backend()


async def save_upload(file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """Convenience function: save a file and return its URL."""
    return await storage.save(file_bytes, filename, content_type)
