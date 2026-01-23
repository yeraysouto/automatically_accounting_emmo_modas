from __future__ import annotations

"""Reference code helpers.

We use `reference_code` as the stable identifier to join OCR lines to the
article master. This module provides:

- `generate_reference_code`: deterministic fallback when OCR doesn't provide one.
- `normalize_reference_code`: canonicalize to `<SUP>_<CODE>` to avoid collisions
    across suppliers.
"""

import base64
import hashlib
import re
from typing import Optional

from app.settings import get_settings


def _supplier_prefix(name_supplier: str | None, prefix_len: int) -> str:
    """Derive a stable uppercase prefix from supplier name."""
    if not name_supplier:
        return "SUP"
    cleaned = re.sub(r"[^A-Za-z]", "", name_supplier).upper()
    return (cleaned[:prefix_len] or "SUP").ljust(prefix_len, "X")


def _hash64(value: str, length: int) -> str:
    """Compute a URL-safe base64 sha256 hash, truncated to `length`."""
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    b64 = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return b64[:length]


def generate_reference_code(
    *,
    name_supplier: str | None,
    description: str | None,
    num_invoice: str | None,
) -> Optional[str]:
    """Generate a deterministic reference code for human review.

    This is a fallback when OCR fails to provide a supplier reference.
    The output is stable for the same (supplier, description, invoice number).
    """
    if not description and not num_invoice:
        return None

    settings = get_settings()
    prefix = _supplier_prefix(name_supplier, settings.reference_code_prefix_len)
    seed = "|".join([name_supplier or "", description or "", num_invoice or ""]).strip()
    if not seed:
        return None
    hashed = _hash64(seed, settings.reference_code_hash_len)
    return f"{prefix}_{hashed}"


def normalize_reference_code(*, name_supplier: str | None, reference_code: str | None) -> Optional[str]:
    """Return canonical reference code.

    Rule: always store as <SUP>_<CODE> where SUP is derived from supplier name.
    If reference_code already matches that pattern, it is returned unchanged.
    """

    if reference_code is None:
        return None
    raw = reference_code.strip()
    if not raw:
        return None

    settings = get_settings()
    prefix = _supplier_prefix(name_supplier, settings.reference_code_prefix_len)
    # Already canonical? Keep it.
    if re.fullmatch(r"[A-Z]{%d}_.+" % settings.reference_code_prefix_len, raw):
        return raw
    return f"{prefix}_{raw}"

