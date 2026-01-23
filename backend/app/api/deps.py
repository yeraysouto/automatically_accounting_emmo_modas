from __future__ import annotations

"""FastAPI dependencies for security and uploads.

This module centralizes:

- API-key authentication (read/write) via the `X-API-Key` header.
- Upload validation (content-type allowlist) and bounded reads to avoid OOM.

Notes:
- API key comparison uses `hmac.compare_digest` to reduce timing leakage.
- `read_upload_limited` reads in chunks and enforces `max_bytes`.
"""

import hmac
from typing import Iterable

from fastapi import Depends, Header, HTTPException, UploadFile

from app.settings import get_settings


def _split_csv(value: str) -> list[str]:
    """Split a comma-separated config value into normalized tokens."""
    return [v.strip() for v in value.split(",") if v.strip()]


def get_allowed_mime_types() -> set[str]:
    """Return the configured allowed upload mime types as a set."""
    settings = get_settings()
    if not settings.allowed_upload_mime_types:
        return set()
    return set(_split_csv(settings.allowed_upload_mime_types))


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    """Enforce API-key for write operations when configured.

    If `EMMO_API_KEY` is not set or `EMMO_REQUIRE_API_KEY_FOR_WRITE=false`, this
    dependency is a no-op.
    """
    settings = get_settings()
    if settings.api_key is None or not settings.require_api_key_for_write:
        return

    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")


def require_api_key_for_read(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    """Optionally enforce API-key for read operations when configured.

    If `EMMO_REQUIRE_API_KEY_FOR_READ=true`, GET endpoints protected with
    `AuthReadDep` will require `X-API-Key`.
    """
    settings = get_settings()
    if settings.api_key is None or not settings.require_api_key_for_read:
        return

    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")


async def read_upload_limited(file: UploadFile, *, max_bytes: int) -> bytes:
    """Read an uploaded file safely, enforcing a maximum size.

    Args:
        file: FastAPI `UploadFile`.
        max_bytes: Hard limit in bytes.

    Raises:
        HTTPException(413): If the upload exceeds `max_bytes`.
    """
    # UploadFile uses a SpooledTemporaryFile; reading in chunks keeps us safe.
    chunk_size = 1024 * 1024  # 1MB
    total = 0
    out = bytearray()

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="File too large")
        out.extend(chunk)

    return bytes(out)


def validate_upload(file: UploadFile, allowed_mime_types: Iterable[str] | None = None):
    """Validate upload content-type against an allowlist.

    Args:
        file: Uploaded file.
        allowed_mime_types: Optional override allowlist; defaults to settings.

    Raises:
        HTTPException(415): If `file.content_type` is not allowed.
    """
    allowed = set(allowed_mime_types or get_allowed_mime_types())
    if allowed and file.content_type and file.content_type not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {file.content_type}",
        )


AuthDep = Depends(require_api_key)
AuthReadDep = Depends(require_api_key_for_read)
