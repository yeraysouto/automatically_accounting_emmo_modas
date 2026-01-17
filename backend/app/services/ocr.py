from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import httpx

from app.settings import get_settings


@dataclass(frozen=True)
class ParsedInvoice:
    cif_supplier: str
    name_supplier: Optional[str]
    tel_number_supplier: Optional[str]
    email_supplier: Optional[str]
    num_invoice: Optional[str]
    invoice_date: Optional[date]
    total_invoice_amount: Optional[float]
    invoice_type: Optional[str]
    optional_fields: Optional[dict]
    raw_text: Optional[str]


@dataclass(frozen=True)
class ParsedLine:
    reference_code: Optional[str]
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
        settings = get_settings()
        if settings.ocr_api_url:
            return self._parse_via_http(file_bytes=file_bytes, filename=filename)

        return self._parse_stub(file_bytes=file_bytes, filename=filename)

    def _parse_stub(self, file_bytes: bytes, filename: str) -> tuple[ParsedInvoice, list[ParsedLine]]:
        raw_text = f"STUB_OCR filename={filename} bytes={len(file_bytes)}"

        invoice = ParsedInvoice(
            cif_supplier="UNKNOWN",
            name_supplier=None,
            tel_number_supplier=None,
            email_supplier=None,
            num_invoice=None,
            invoice_date=None,
            total_invoice_amount=None,
            invoice_type=None,
            optional_fields=None,
            raw_text=raw_text,
        )

        return invoice, []

    def _parse_via_http(self, file_bytes: bytes, filename: str) -> tuple[ParsedInvoice, list[ParsedLine]]:
        settings = get_settings()
        headers: dict[str, str] = {}
        if settings.ocr_api_key:
            # Common pattern; adjust if your provider uses a different header.
            headers["Authorization"] = f"Bearer {settings.ocr_api_key}"  # noqa: S105

        files = {"file": (filename, file_bytes)}

        with httpx.Client(timeout=settings.ocr_api_timeout_s) as client:
            resp = client.post(settings.ocr_api_url, headers=headers, files=files)
            resp.raise_for_status()
            payload = resp.json()

        return self._normalize_payload(payload, filename=filename)

    def _normalize_payload(self, payload: object, filename: str) -> tuple[ParsedInvoice, list[ParsedLine]]:
        """Normalize many possible OCR API response shapes.

        Supported shapes (best-effort):
        - {"invoice": {...}, "lines": [{...}, ...]}
        - {"raw_text": "..."}
        - Anything else: stored into raw_text (stringified)

        Invoice keys we look for (any of these):
        - cif_supplier, name_supplier, tel_number_supplier, email_supplier
        - num_invoice, date, total_invoice_amount, invoice_type, optional_fields, raw_text
        Line keys we look for:
        - reference_code, description, quantity, price, total_no_iva
        """

        raw_text = None
        invoice_obj: dict[str, object] = {}
        lines_obj: list[object] = []

        if isinstance(payload, dict):
            if isinstance(payload.get("invoice"), dict):
                invoice_obj = payload["invoice"]  # type: ignore[assignment]
            if isinstance(payload.get("lines"), list):
                lines_obj = payload["lines"]  # type: ignore[assignment]
            if isinstance(payload.get("raw_text"), str):
                raw_text = payload.get("raw_text")  # type: ignore[assignment]

        if raw_text is None:
            raw_text = str(payload)

        cif_supplier = "UNKNOWN"
        if isinstance(invoice_obj.get("cif_supplier"), str) and invoice_obj["cif_supplier"]:
            cif_supplier = str(invoice_obj["cif_supplier"])

        invoice_date = None
        if isinstance(invoice_obj.get("date"), str):
            # Accept ISO format if provider sends it
            try:
                invoice_date = date.fromisoformat(str(invoice_obj["date"]))
            except ValueError:
                invoice_date = None

        total_invoice_amount = None
        if invoice_obj.get("total_invoice_amount") is not None:
            try:
                total_invoice_amount = float(invoice_obj["total_invoice_amount"])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                total_invoice_amount = None
        elif invoice_obj.get("total_supplier") is not None:
            try:
                total_invoice_amount = float(invoice_obj["total_supplier"])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                total_invoice_amount = None

        invoice = ParsedInvoice(
            cif_supplier=cif_supplier,
            name_supplier=str(invoice_obj["name_supplier"]) if isinstance(invoice_obj.get("name_supplier"), str) else None,
            tel_number_supplier=str(invoice_obj["tel_number_supplier"]) if isinstance(invoice_obj.get("tel_number_supplier"), str) else None,
            email_supplier=str(invoice_obj["email_supplier"]) if isinstance(invoice_obj.get("email_supplier"), str) else None,
            num_invoice=str(invoice_obj["num_invoice"]) if isinstance(invoice_obj.get("num_invoice"), str) else None,
            invoice_date=invoice_date,
            total_invoice_amount=total_invoice_amount,
            invoice_type=str(invoice_obj["invoice_type"]) if isinstance(invoice_obj.get("invoice_type"), str) else None,
            optional_fields=invoice_obj.get("optional_fields") if isinstance(invoice_obj.get("optional_fields"), dict) else None,
            raw_text=raw_text or f"OCR filename={filename}",
        )

        parsed_lines: list[ParsedLine] = []
        for item in lines_obj:
            if not isinstance(item, dict):
                continue
            reference = item.get("reference_code")
            if isinstance(reference, str):
                reference = reference.strip() or None
            else:
                reference = None

            quantity = None
            if item.get("quantity") is not None:
                try:
                    quantity = int(item["quantity"])  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    quantity = None

            price = None
            if item.get("price") is not None:
                try:
                    price = float(item["price"])  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    price = None

            total_no_iva = None
            if item.get("total_no_iva") is not None:
                try:
                    total_no_iva = float(item["total_no_iva"])  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    total_no_iva = None

            parsed_lines.append(
                ParsedLine(
                    reference_code=reference,
                    description=str(item["description"]) if isinstance(item.get("description"), str) else None,
                    quantity=quantity,
                    price=price,
                    total_no_iva=total_no_iva,
                )
            )

        return invoice, parsed_lines
