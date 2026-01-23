from __future__ import annotations

"""HTTP API routes.

This module defines the FastAPI endpoints for:

- Ingesting invoices (file upload or pre-parsed OCR JSON).
- Managing invoice lines and reference codes.
- Upserting and reading the Montcau article master.
- Exporting invoice lines to a Montcau-compatible import payload.

Security:
- Write endpoints use `AuthDep` (API key required by default when configured).
- Read endpoints can optionally require API key via `AuthReadDep`.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    ArticleOut,
    ArticleUpsert,
    ClothesLineCreate,
    ClothesLineOut,
    InvoiceCreate,
    InvoiceOut,
    InvoiceStatusUpdate,
    IngestInvoiceOcr,
    IngestLineOcr,
    LineSetReference,
    ProcessInvoiceResult,
)
from app.db.models import DataOcrInvoice, ImportacionArticulosMontcau, OcrInfoClothes, PriceObservation
from app.db.session import get_db
from app.settings import get_settings
from app.api.deps import AuthDep, AuthReadDep, read_upload_limited, validate_upload
from app.services.ocr import OcrService
from app.services.pricing import apply_price_decision, evaluate_price
from app.services.reference_code import generate_reference_code, normalize_reference_code
from app.services.storage import save_invoice_upload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    """Basic liveness check."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Database connectivity check.

    Returns 503 if the database cannot execute a trivial query.
    """
    try:
        value = db.execute(select(1)).scalar_one()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"db_unhealthy: {exc}")
    return {"status": "ok", "db": value}


@router.post("/invoices", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db), _: None = AuthDep):
    invoice = DataOcrInvoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cif_supplier: str | None = None,
    status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    db: Session = Depends(get_db),
    _: None = AuthReadDep,
):
    """List invoices with simple pagination and filters."""
    q = select(DataOcrInvoice)
    if cif_supplier:
        q = q.where(DataOcrInvoice.cif_supplier == cif_supplier)
    if status:
        q = q.where(DataOcrInvoice.status == status)
    if created_from:
        q = q.where(DataOcrInvoice.created_at >= created_from)
    if created_to:
        q = q.where(DataOcrInvoice.created_at <= created_to)

    q = q.order_by(DataOcrInvoice.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(q).all())


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), _: None = AuthReadDep):
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/invoices/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    _: None = AuthDep,
):
    """Update invoice workflow status.

    This is intended for manual review flows (e.g., after OCR errors).
    """
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = payload.status
    if payload.clear_error:
        invoice.last_error_code = None
        invoice.last_error_message = None
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices/{invoice_id}/download")
def download_invoice_file(invoice_id: int, db: Session = Depends(get_db), _: None = AuthReadDep):
    """Download the original stored invoice file.

    The path is validated to be under `storage_root` to prevent path traversal.
    """
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not invoice.invoice_file_path:
        raise HTTPException(status_code=404, detail="Invoice has no stored file")

    rel_path = Path(invoice.invoice_file_path)
    if rel_path.is_absolute():
        raise HTTPException(status_code=400, detail="Invalid stored path")

    settings = get_settings()
    storage_root = Path(settings.storage_root).resolve()
    abs_path = (storage_root / rel_path).resolve()
    if storage_root not in abs_path.parents and abs_path != storage_root:
        raise HTTPException(status_code=400, detail="Invalid stored path")
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Stored file missing on disk")

    return FileResponse(
        path=str(abs_path),
        media_type=invoice.invoice_file_mime_type or "application/octet-stream",
        filename=invoice.invoice_file_name or abs_path.name,
    )


@router.post("/invoices/{invoice_id}/lines", response_model=ClothesLineOut)
def add_invoice_line(
    invoice_id: int,
    payload: ClothesLineCreate,
    db: Session = Depends(get_db),
    _: None = AuthDep,
):
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line = OcrInfoClothes(invoice_id=invoice_id, **payload.model_dump())
    if line.reference_code:
        line.reference_code_raw = line.reference_code
        if get_settings().enforce_reference_code_prefix:
            line.reference_code = normalize_reference_code(
                name_supplier=line.name_supplier,
                reference_code=line.reference_code,
            )
        if line.reference_code_origin is None:
            line.reference_code_origin = "manual"
    if line.reference_code is None and get_settings().auto_reference_code:
        line.reference_code = generate_reference_code(
            name_supplier=line.name_supplier,
            description=line.description,
            num_invoice=line.num_invoice,
        )
        if line.reference_code:
            line.reference_code_origin = "auto"
    db.add(line)
    db.flush()

    if line.price is not None and line.reference_code:
        db.add(
            PriceObservation(
                cif_supplier=line.cif_supplier,
                reference_code=line.reference_code,
                observed_price=float(line.price),
                invoice_id=invoice_id,
                line_id=line.id,
            )
        )

    article = None
    if line.reference_code:
        q = select(ImportacionArticulosMontcau).where(
            ImportacionArticulosMontcau.reference_code == line.reference_code
        )
        article = db.scalars(q).first()
        decision = evaluate_price(db=db, line=line, article=article)
        apply_price_decision(line, decision)
        if decision.flag:
            logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate reference_code for this invoice")

    db.refresh(line)
    return line


@router.post("/invoices/{invoice_id}/lines/{line_id}/set-reference", response_model=ClothesLineOut)
def set_line_reference(
    invoice_id: int,
    line_id: int,
    payload: LineSetReference,
    db: Session = Depends(get_db),
    _: None = AuthDep,
):
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line = db.get(OcrInfoClothes, line_id)
    if not line or line.invoice_id != invoice_id:
        raise HTTPException(status_code=404, detail="Line not found")

    line.reference_code_raw = payload.reference_code
    line.reference_code = (
        normalize_reference_code(name_supplier=line.name_supplier, reference_code=payload.reference_code)
        if get_settings().enforce_reference_code_prefix
        else payload.reference_code
    )
    line.reference_code_origin = "manual"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate reference_code for this invoice")

    # Upsert minimal article now that we have a reference
    q = select(ImportacionArticulosMontcau).where(
        ImportacionArticulosMontcau.reference_code == line.reference_code
    )
    article = db.scalars(q).first()
    if article is None:
        article = ImportacionArticulosMontcau(
            reference_code=line.reference_code,
            descripcion=line.description,
            cantidad=line.quantity,
            coste_unitario=line.price,
        )
        db.add(article)
        db.commit()

    if line.price is not None and line.reference_code:
        try:
            db.add(
                PriceObservation(
                    cif_supplier=line.cif_supplier,
                    reference_code=line.reference_code,
                    observed_price=float(line.price),
                    invoice_id=invoice_id,
                    line_id=line.id,
                )
            )
            db.commit()
        except IntegrityError:
            db.rollback()

    db.refresh(line)
    return line


@router.post("/ingest/invoice", response_model=ProcessInvoiceResult)
def ingest_invoice_ocr(payload: IngestInvoiceOcr, db: Session = Depends(get_db), _: None = AuthDep):
    """Ingest a pre-parsed OCR payload (e.g., WhatsApp/Telegram integration).

    The request is expected to contain the already extracted invoice header and
    (optionally) its lines, with or without `reference_code`.

    Side effects:
    - Creates an invoice and persists all provided lines.
    - Normalizes `reference_code` to the canonical format (when enabled).
    - Upserts article master rows when a `reference_code` is present.
    - Appends price observations (`PriceObservation`) when both price and
      `reference_code` are present.
    - Evaluates pricing rules and updates `price_flag` accordingly.

    Args:
        payload: Invoice header and lines extracted by OCR.
        db: SQLAlchemy session.

    Returns:
        The saved invoice, its saved lines, and the number of articles upserted.
    """

    with db.begin():
        invoice = DataOcrInvoice(
            cif_supplier=payload.cif_supplier,
            name_supplier=payload.name_supplier,
            tel_number_supplier=payload.tel_number_supplier,
            email_supplier=payload.email_supplier,
            num_invoice=payload.num_invoice,
            total_invoice_amount=payload.total_invoice_amount,
            invoice_type=payload.invoice_type,
            optional_fields=payload.optional_fields,
            raw_text=payload.raw_text,
            source_channel=payload.source_channel,
            source_thread_id=payload.source_thread_id,
            source_message_id=payload.source_message_id,
            status="draft",
        )
        db.add(invoice)
        db.flush()

        out_lines: list[OcrInfoClothes] = []
        for ln in payload.lines:
            line = OcrInfoClothes(invoice_id=invoice.id, **ln.model_dump())
            if line.reference_code:
                line.reference_code_raw = line.reference_code
                if get_settings().enforce_reference_code_prefix:
                    line.reference_code = normalize_reference_code(
                        name_supplier=line.name_supplier,
                        reference_code=line.reference_code,
                    )
                if line.reference_code_origin is None:
                    line.reference_code_origin = "ocr"
            if line.reference_code is None and get_settings().auto_reference_code:
                line.reference_code = generate_reference_code(
                    name_supplier=line.name_supplier,
                    description=line.description,
                    num_invoice=line.num_invoice,
                )
                if line.reference_code:
                    line.reference_code_origin = "auto"
            db.add(line)
            out_lines.append(line)

        db.flush()
        for line in out_lines:
            if line.price is not None and line.reference_code:
                db.add(
                    PriceObservation(
                        cif_supplier=line.cif_supplier,
                        reference_code=line.reference_code,
                        observed_price=float(line.price),
                        invoice_id=invoice.id,
                        line_id=line.id,
                    )
                )

        upserted = 0
        for line in out_lines:
            if not line.reference_code:
                continue
            q = select(ImportacionArticulosMontcau).where(
                ImportacionArticulosMontcau.reference_code == line.reference_code
            )
            article = db.scalars(q).first()
            if article is None:
                article = ImportacionArticulosMontcau(
                    reference_code=line.reference_code,
                    descripcion=line.description,
                    cantidad=line.quantity,
                    coste_unitario=line.price,
                )
                db.add(article)
                upserted += 1
            else:
                if line.description is not None:
                    article.descripcion = line.description
                if line.quantity is not None:
                    article.cantidad = line.quantity
                if line.price is not None:
                    article.coste_unitario = line.price

            decision = evaluate_price(db=db, line=line, article=article)
            apply_price_decision(line, decision)
            if decision.flag:
                logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})

    db.refresh(invoice)
    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice.id).order_by(OcrInfoClothes.id)
    saved_lines = list(db.scalars(q).all())
    return ProcessInvoiceResult(invoice=invoice, lines=saved_lines, articles_upserted=upserted)


@router.post("/ingest/line", response_model=ClothesLineOut)
def ingest_line_ocr(payload: IngestLineOcr, db: Session = Depends(get_db), _: None = AuthDep):
    """Ingest a single OCR line (garment) for an existing invoice.

    Side effects:
    - Persists the line and keeps traceability via `reference_code_raw`.
    - Normalizes `reference_code` to the canonical format (when enabled).
    - Appends a `PriceObservation` record for historical tracking when both
      price and `reference_code` are present.

    Args:
        payload: Target invoice id and a single parsed line.
        db: SQLAlchemy session.

    Returns:
        The saved invoice line.

    Raises:
        HTTPException(404): If the invoice does not exist.
        HTTPException(409): If the normalized reference duplicates within invoice.
    """

    invoice = db.get(DataOcrInvoice, payload.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line_payload = payload.line
    line = OcrInfoClothes(invoice_id=invoice.id, **line_payload.model_dump())
    if line.reference_code:
        line.reference_code_raw = line.reference_code
        if get_settings().enforce_reference_code_prefix:
            line.reference_code = normalize_reference_code(
                name_supplier=line.name_supplier,
                reference_code=line.reference_code,
            )
        if line.reference_code_origin is None:
            line.reference_code_origin = "ocr"
    if line.reference_code is None and get_settings().auto_reference_code:
        line.reference_code = generate_reference_code(
            name_supplier=line.name_supplier,
            description=line.description,
            num_invoice=line.num_invoice,
        )
        if line.reference_code:
            line.reference_code_origin = "auto"
    db.add(line)
    db.flush()

    if line.price is not None and line.reference_code:
        db.add(
            PriceObservation(
                cif_supplier=line.cif_supplier,
                reference_code=line.reference_code,
                observed_price=float(line.price),
                invoice_id=invoice.id,
                line_id=line.id,
            )
        )

    article = None
    if line.reference_code:
        q = select(ImportacionArticulosMontcau).where(
            ImportacionArticulosMontcau.reference_code == line.reference_code
        )
        article = db.scalars(q).first()
        decision = evaluate_price(db=db, line=line, article=article)
        apply_price_decision(line, decision)
        if decision.flag:
            logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate reference_code for this invoice")
    db.refresh(line)
    return line


@router.get("/invoices/{invoice_id}/lines", response_model=list[ClothesLineOut])
def list_invoice_lines(invoice_id: int, db: Session = Depends(get_db), _: None = AuthReadDep):
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice_id).order_by(OcrInfoClothes.id)
    return list(db.scalars(q).all())


@router.put("/articles", response_model=ArticleOut)
def upsert_article(payload: ArticleUpsert, db: Session = Depends(get_db), _: None = AuthDep):
    q = select(ImportacionArticulosMontcau).where(
        ImportacionArticulosMontcau.reference_code == payload.reference_code
    )
    article = db.scalars(q).first()

    if article is None:
        article = ImportacionArticulosMontcau(**payload.model_dump())
        db.add(article)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Article with reference_code already exists")
        db.refresh(article)
        return article

    for k, v in payload.model_dump().items():
        setattr(article, k, v)

    db.commit()
    db.refresh(article)
    return article


@router.get("/articles/{reference_code}", response_model=ArticleOut)
def get_article(reference_code: str, db: Session = Depends(get_db), _: None = AuthReadDep):
    q = select(ImportacionArticulosMontcau).where(ImportacionArticulosMontcau.reference_code == reference_code)
    article = db.scalars(q).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/invoices/{invoice_id}/export/importacion-montcau", response_model=list[ArticleUpsert])
def export_importacion_montcau(invoice_id: int, db: Session = Depends(get_db), _: None = AuthReadDep):
    """Export invoice lines into Importación Artículos Montcau rows (JSON).

    This does not write to the article master; it only returns rows ready to import.
    """

    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice_id).order_by(OcrInfoClothes.id)
    lines = list(db.scalars(q).all())

    out: list[ArticleUpsert] = []
    for ln in lines:
        if not ln.reference_code:
            continue
        out.append(
            ArticleUpsert(
                reference_code=ln.reference_code,
                descripcion=ln.description,
                cantidad=ln.quantity,
                coste_unitario=ln.price,
            )
        )
    return out


@router.post("/process/invoice", response_model=ProcessInvoiceResult)
async def process_invoice(file: UploadFile = File(...), db: Session = Depends(get_db), _: None = AuthDep):
    """Process an uploaded invoice end-to-end.

    Flow:
    1) Upload invoice file
    2) OCR parse (stub for now)
    3) Save invoice to `data_ocr_invoice`
    4) Save detected lines to `ocr_info_clothes`
    5) Upsert basic articles into `importacion_articulos_montcau` (by `reference_code`)

    Error policy:
    - If OCR fails, the flow falls back to a stub parse and marks the invoice as
      `needs_review` with `last_error_*` fields populated.

    Args:
        file: Uploaded invoice file.
        db: SQLAlchemy session.

    Returns:
        The saved invoice, its saved lines, and the number of articles upserted.

    Raises:
        HTTPException(413): If the upload exceeds the configured max size.
        HTTPException(415): If the upload content-type is not allowed.
    """

    validate_upload(file)
    file_bytes = await read_upload_limited(file, max_bytes=get_settings().max_upload_bytes)
    ocr = OcrService()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    try:
        parsed_invoice, parsed_lines = ocr.parse(file_bytes, filename=file.filename or "uploaded")
        ocr_error: tuple[str, str] | None = None
    except Exception as exc:  # noqa: BLE001
        parsed_invoice, parsed_lines = ocr._parse_stub(file_bytes=file_bytes, filename=file.filename or "uploaded")
        ocr_error = ("ocr_failed", str(exc))
    stored_path = save_invoice_upload(
        file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        invoice_date=parsed_invoice.invoice_date,
    )

    with db.begin():
        invoice = DataOcrInvoice(
            cif_supplier=parsed_invoice.cif_supplier,
            name_supplier=parsed_invoice.name_supplier,
            tel_number_supplier=parsed_invoice.tel_number_supplier,
            email_supplier=parsed_invoice.email_supplier,
            num_invoice=parsed_invoice.num_invoice,
            total_invoice_amount=parsed_invoice.total_invoice_amount,
            invoice_type=parsed_invoice.invoice_type,
            optional_fields=parsed_invoice.optional_fields,
            raw_text=parsed_invoice.raw_text,
            status="needs_review" if ocr_error else "draft",
            last_error_code=ocr_error[0] if ocr_error else None,
            last_error_message=ocr_error[1] if ocr_error else None,
            invoice_file_path=stored_path,
            invoice_file_name=file.filename,
            invoice_file_mime_type=file.content_type,
            invoice_file_sha256=file_sha256,
            invoice_file_bytes=len(file_bytes),
        )
        db.add(invoice)
        db.flush()

        out_lines: list[OcrInfoClothes] = []
        for ln in parsed_lines:
            line = OcrInfoClothes(
                invoice_id=invoice.id,
                cif_supplier=invoice.cif_supplier,
                name_supplier=invoice.name_supplier,
                num_invoice=invoice.num_invoice,
                date=parsed_invoice.invoice_date,
                reference_code_raw=ln.reference_code,
                reference_code=ln.reference_code,
                description=ln.description,
                quantity=ln.quantity,
                price=ln.price,
                total_no_iva=ln.total_no_iva,
            )
            if line.reference_code:
                if get_settings().enforce_reference_code_prefix:
                    line.reference_code = normalize_reference_code(
                        name_supplier=line.name_supplier,
                        reference_code=line.reference_code,
                    )
                if line.reference_code_origin is None:
                    line.reference_code_origin = "ocr"
            if line.reference_code is None and get_settings().auto_reference_code:
                line.reference_code = generate_reference_code(
                    name_supplier=line.name_supplier,
                    description=line.description,
                    num_invoice=line.num_invoice,
                )
                if line.reference_code:
                    line.reference_code_origin = "auto"
            db.add(line)
            out_lines.append(line)

        db.flush()
        for line in out_lines:
            if line.price is not None and line.reference_code:
                db.add(
                    PriceObservation(
                        cif_supplier=line.cif_supplier,
                        reference_code=line.reference_code,
                        observed_price=float(line.price),
                        invoice_id=invoice.id,
                        line_id=line.id,
                    )
                )

        # Upsert minimal articles (reference_code + description + quantity/cost)
        upserted = 0
        for line in out_lines:
            if not line.reference_code:
                continue
            q = select(ImportacionArticulosMontcau).where(
                ImportacionArticulosMontcau.reference_code == line.reference_code
            )
            article = db.scalars(q).first()

            if article is None:
                article = ImportacionArticulosMontcau(
                    reference_code=line.reference_code,
                    descripcion=line.description,
                    cantidad=line.quantity,
                    coste_unitario=line.price,
                )
                db.add(article)
                upserted += 1
            else:
                if line.description is not None:
                    article.descripcion = line.description
                if line.quantity is not None:
                    article.cantidad = line.quantity
                if line.price is not None:
                    article.coste_unitario = line.price

            decision = evaluate_price(db=db, line=line, article=article)
            apply_price_decision(line, decision)
            if decision.flag:
                logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})

    db.refresh(invoice)
    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice.id).order_by(OcrInfoClothes.id)
    saved_lines = list(db.scalars(q).all())

    return ProcessInvoiceResult(invoice=invoice, lines=saved_lines, articles_upserted=upserted)


@router.post("/invoices/{invoice_id}/process", response_model=ProcessInvoiceResult)
async def reprocess_invoice(
    invoice_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = AuthDep,
):
    """Reprocesa una factura existente con una nueva foto/archivo.

    - Actualiza campos de cabecera si vienen del OCR
    - Reemplaza las líneas existentes
    - Hace upsert de artículos por reference_code
    """

    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    validate_upload(file)
    file_bytes = await read_upload_limited(file, max_bytes=get_settings().max_upload_bytes)
    ocr = OcrService()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    try:
        parsed_invoice, parsed_lines = ocr.parse(file_bytes, filename=file.filename or "uploaded")
        ocr_error: tuple[str, str] | None = None
    except Exception as exc:  # noqa: BLE001
        parsed_invoice, parsed_lines = ocr._parse_stub(file_bytes=file_bytes, filename=file.filename or "uploaded")
        ocr_error = ("ocr_failed", str(exc))
    stored_path = save_invoice_upload(
        file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        invoice_date=parsed_invoice.invoice_date,
    )

    # Update header (only overwrite when OCR provides something)
    if parsed_invoice.cif_supplier and parsed_invoice.cif_supplier != "UNKNOWN":
        invoice.cif_supplier = parsed_invoice.cif_supplier
    if parsed_invoice.name_supplier is not None:
        invoice.name_supplier = parsed_invoice.name_supplier
    if parsed_invoice.tel_number_supplier is not None:
        invoice.tel_number_supplier = parsed_invoice.tel_number_supplier
    if parsed_invoice.email_supplier is not None:
        invoice.email_supplier = parsed_invoice.email_supplier
    if parsed_invoice.num_invoice is not None:
        invoice.num_invoice = parsed_invoice.num_invoice
    if parsed_invoice.total_invoice_amount is not None:
        invoice.total_invoice_amount = parsed_invoice.total_invoice_amount
    if parsed_invoice.invoice_type is not None:
        invoice.invoice_type = parsed_invoice.invoice_type
    if parsed_invoice.optional_fields is not None:
        invoice.optional_fields = parsed_invoice.optional_fields
    if parsed_invoice.raw_text is not None:
        invoice.raw_text = parsed_invoice.raw_text
    if stored_path is not None:
        invoice.invoice_file_path = stored_path
        invoice.invoice_file_name = file.filename
        invoice.invoice_file_mime_type = file.content_type
        invoice.invoice_file_sha256 = file_sha256
        invoice.invoice_file_bytes = len(file_bytes)

    if ocr_error:
        invoice.status = "needs_review"
        invoice.last_error_code = ocr_error[0]
        invoice.last_error_message = ocr_error[1]

    with db.begin():
        # Replace lines
        existing = list(
            db.scalars(select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice_id)).all()
        )
        for ln in existing:
            db.delete(ln)
        db.flush()

        new_lines: list[OcrInfoClothes] = []
        for ln in parsed_lines:
            line = OcrInfoClothes(
                invoice_id=invoice.id,
                cif_supplier=invoice.cif_supplier,
                name_supplier=invoice.name_supplier,
                num_invoice=invoice.num_invoice,
                date=parsed_invoice.invoice_date,
                reference_code_raw=ln.reference_code,
                reference_code=ln.reference_code,
                description=ln.description,
                quantity=ln.quantity,
                price=ln.price,
                total_no_iva=ln.total_no_iva,
            )
            if line.reference_code:
                if get_settings().enforce_reference_code_prefix:
                    line.reference_code = normalize_reference_code(
                        name_supplier=line.name_supplier,
                        reference_code=line.reference_code,
                    )
                if line.reference_code_origin is None:
                    line.reference_code_origin = "ocr"
            if line.reference_code is None and get_settings().auto_reference_code:
                line.reference_code = generate_reference_code(
                    name_supplier=line.name_supplier,
                    description=line.description,
                    num_invoice=line.num_invoice,
                )
                if line.reference_code:
                    line.reference_code_origin = "auto"
            db.add(line)
            new_lines.append(line)

        db.flush()
        for line in new_lines:
            if line.price is not None and line.reference_code:
                db.add(
                    PriceObservation(
                        cif_supplier=line.cif_supplier,
                        reference_code=line.reference_code,
                        observed_price=float(line.price),
                        invoice_id=invoice.id,
                        line_id=line.id,
                    )
                )

        # Upsert minimal articles
        upserted = 0
        for line in new_lines:
            if not line.reference_code:
                continue
            q = select(ImportacionArticulosMontcau).where(
                ImportacionArticulosMontcau.reference_code == line.reference_code
            )
            article = db.scalars(q).first()
            if article is None:
                article = ImportacionArticulosMontcau(
                    reference_code=line.reference_code,
                    descripcion=line.description,
                    cantidad=line.quantity,
                    coste_unitario=line.price,
                )
                db.add(article)
                upserted += 1
            else:
                if line.description is not None:
                    article.descripcion = line.description
                if line.quantity is not None:
                    article.cantidad = line.quantity
                if line.price is not None:
                    article.coste_unitario = line.price

            decision = evaluate_price(db=db, line=line, article=article)
            apply_price_decision(line, decision)
            if decision.flag:
                logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})

    db.refresh(invoice)

    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice.id).order_by(OcrInfoClothes.id)
    saved_lines = list(db.scalars(q).all())

    return ProcessInvoiceResult(invoice=invoice, lines=saved_lines, articles_upserted=upserted)
