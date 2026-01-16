from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class ParsedInvoice:
    cif_supplier: str
    name_supplier: Optional[str]
    tel_number_supplier: Optional[str]
    email_supplier: Optional[str]
    num_invoice: Optional[str]
    invoice_date: Optional[date]
    total_supplier: Optional[float]
    raw_text: Optional[str]


@dataclass(frozen=True)
class ParsedLine:
    reference_code: str
    description: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    total_no_iva: Optional[float]


class OcrService:
    """OCR parsing facade.

    This is intentionally a stub: plug in your OCR provider later (Azure Document
    Intelligence, Tesseract, Google Vision, etc.).
    """

    def parse(self, file_bytes: bytes, filename: str) -> tuple[ParsedInvoice, list[ParsedLine]]:
        # Minimal placeholder implementation.
        # For now, we store the raw bytes size and filename in raw_text so the pipeline works.
        raw_text = f"STUB_OCR filename={filename} bytes={len(file_bytes)}"

        invoice = ParsedInvoice(
            cif_supplier="UNKNOWN",
            name_supplier=None,
            tel_number_supplier=None,
            email_supplier=None,
            num_invoice=None,
            invoice_date=None,
            total_supplier=None,
            raw_text=raw_text,
        )

        # No lines detected in stub
        return invoice, []
