from __future__ import annotations

from typing import Iterable

from fastapi import Depends, Header, HTTPException, UploadFile

from app.settings import get_settings


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def get_allowed_mime_types() -> set[str]:
    settings = get_settings()
    if not settings.allowed_upload_mime_types:
        return set()
    return set(_split_csv(settings.allowed_upload_mime_types))


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    settings = get_settings()
    if settings.api_key is None:
        return

    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def read_upload_limited(file: UploadFile, *, max_bytes: int) -> bytes:
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
    allowed = set(allowed_mime_types or get_allowed_mime_types())
    if allowed and file.content_type and file.content_type not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {file.content_type}",
        )


AuthDep = Depends(require_api_key)
