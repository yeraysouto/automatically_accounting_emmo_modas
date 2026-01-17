from __future__ import annotations

import base64
import hashlib
import re
from typing import Optional

from app.settings import get_settings


def _supplier_prefix(name_supplier: str | None, prefix_len: int) -> str:
    if not name_supplier:
        return "SUP"
    cleaned = re.sub(r"[^A-Za-z]", "", name_supplier).upper()
    return (cleaned[:prefix_len] or "SUP").ljust(prefix_len, "X")


def _hash64(value: str, length: int) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    b64 = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return b64[:length]


def generate_reference_code(
    *,
    name_supplier: str | None,
    description: str | None,
    num_invoice: str | None,
) -> Optional[str]:
    if not description and not num_invoice:
        return None

    settings = get_settings()
    prefix = _supplier_prefix(name_supplier, settings.reference_code_prefix_len)
    seed = "|".join([name_supplier or "", description or "", num_invoice or ""]).strip()
    if not seed:
        return None
    hashed = _hash64(seed, settings.reference_code_hash_len)
    return f"{prefix}_{hashed}"
