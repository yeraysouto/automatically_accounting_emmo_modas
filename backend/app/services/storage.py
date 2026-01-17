from __future__ import annotations

import mimetypes
import os
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from app.settings import get_settings


def _safe_ext(filename: str | None, mime_type: str | None) -> str:
    if filename:
        _, ext = os.path.splitext(filename)
        if ext:
            return ext.lower()
    if mime_type:
        guessed = mimetypes.guess_extension(mime_type)
        if guessed:
            return guessed
    return ".bin"


def _quarter_from_date(value: date | None) -> tuple[int, str]:
    if value is None:
        value = datetime.utcnow().date()
    q = (value.month - 1) // 3 + 1
    return value.year, f"Q{q}"


def save_invoice_upload(
    file_bytes: bytes,
    *,
    filename: str | None,
    mime_type: str | None,
    invoice_date: date | None,
) -> str | None:
    settings = get_settings()
    if not settings.store_uploads:
        return None

    year, quarter = _quarter_from_date(invoice_date)
    ext = _safe_ext(filename, mime_type)
    file_id = uuid4().hex

    relative_path = Path("invoices") / str(year) / quarter / f"{file_id}{ext}"
    absolute_path = Path(settings.storage_root) / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(file_bytes)

    return str(relative_path)
