from __future__ import annotations

"""Optional OCR provider (stub).

This is a separate FastAPI app that simulates an OCR provider.
The main backend can call it via `EMMO_OCR_API_URL`.

Best-effort feature:
- If the upload is an image and `pytesseract` + `Pillow` are available, it will
    extract `raw_text` using Tesseract.

Otherwise it returns a stub payload with the expected response shape:
`{"invoice": {...}, "lines": [...]}`.
"""

from fastapi import Depends, FastAPI, File, UploadFile

from app.api.deps import AuthDep, read_upload_limited, validate_upload
from app.settings import get_settings


def _try_tesseract_ocr(*, content: bytes, mime_type: str | None) -> str | None:
    """Try to extract raw text from an image using Tesseract if installed."""
    if not mime_type or not mime_type.startswith("image/"):
        return None

    try:
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore
    except Exception:  # noqa: BLE001
        return None

    try:
        import io

        img = Image.open(io.BytesIO(content))
        return pytesseract.image_to_string(img)
    except Exception:  # noqa: BLE001
        return None


def create_app() -> FastAPI:
    """Create the OCR provider FastAPI app."""
    app = FastAPI(title="EMMO OCR Provider API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ocr/invoice")
    async def ocr_invoice(file: UploadFile = File(...), _: None = AuthDep):
        # Stub provider: this is where you'd integrate Azure Document Intelligence,
        # Tesseract, etc. For now it returns a valid payload shape.
        validate_upload(file)
        settings = get_settings()
        content = await read_upload_limited(file, max_bytes=settings.max_upload_bytes)

        raw_text = _try_tesseract_ocr(content=content, mime_type=file.content_type)
        if not raw_text:
            raw_text = f"STUB_PROVIDER filename={file.filename} bytes={len(content)}"

        return {
            "invoice": {
                "cif_supplier": "UNKNOWN",
                "name_supplier": None,
                "tel_number_supplier": None,
                "email_supplier": None,
                "num_invoice": None,
                "date": None,
                "total_invoice_amount": None,
                "invoice_type": None,
                "optional_fields": None,
                "raw_text": raw_text,
            },
            "lines": [],
        }

    return app


app = create_app()
