from __future__ import annotations

from fastapi import Depends, FastAPI, File, UploadFile

from app.api.deps import AuthDep, read_upload_limited, validate_upload
from app.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="EMMA OCR Provider API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ocr/invoice")
    async def ocr_invoice(file: UploadFile = File(...), _: None = AuthDep):
        # Stub provider: this is where you'd integrate Azure Document Intelligence,
        # Tesseract, etc. For now it returns a valid payload shape.
        validate_upload(file)
        content = await read_upload_limited(file, max_bytes=settings.max_upload_bytes)
        raw_text = f"STUB_PROVIDER filename={file.filename} bytes={len(content)}"

        return {
            "invoice": {
                "cif_supplier": "UNKNOWN",
                "name_supplier": None,
                "tel_number_supplier": None,
                "email_supplier": None,
                "num_invoice": None,
                "date": None,
                "total_supplier": None,
                "raw_text": raw_text,
            },
            "lines": [],
        }

    return app


app = create_app()
