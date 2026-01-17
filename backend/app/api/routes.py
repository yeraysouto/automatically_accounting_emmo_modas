from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
    IngestInvoiceOcr,
    IngestLineOcr,
    LineSetReference,
    ProcessInvoiceResult,
)
from app.db.models import DataOcrInvoice, ImportacionArticulosMontcau, OcrInfoClothes
from app.db.session import get_db
from app.settings import get_settings
from app.api.deps import AuthDep, read_upload_limited, validate_upload
from app.services.ocr import OcrService
from app.services.pricing import apply_price_decision, evaluate_price
from app.services.reference_code import generate_reference_code
from app.services.storage import save_invoice_upload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/invoices", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db), _: None = AuthDep):
    invoice = DataOcrInvoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


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
    if line.reference_code and line.reference_code_origin is None:
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
    article = None
    if line.reference_code:
        q = select(ImportacionArticulosMontcau).where(
            ImportacionArticulosMontcau.reference_code == line.reference_code
        )
        article = db.scalars(q).first()
        decision = evaluate_price(line=line, article=article)
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

    line.reference_code = payload.reference_code
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

    db.refresh(line)
    return line


@router.post("/ingest/invoice", response_model=ProcessInvoiceResult)
def ingest_invoice_ocr(payload: IngestInvoiceOcr, db: Session = Depends(get_db), _: None = AuthDep):
    """Ingesta de OCR que llega por WhatsApp/Telegram.

    Espera la cabecera ya extraída y opcionalmente líneas (con o sin reference_code).
    Crea una factura y guarda líneas; hace upsert de artículos cuando haya reference_code.
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
            if line.reference_code and line.reference_code_origin is None:
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

            decision = evaluate_price(line=line, article=article)
            apply_price_decision(line, decision)
            if decision.flag:
                logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})

    db.refresh(invoice)
    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice.id).order_by(OcrInfoClothes.id)
    saved_lines = list(db.scalars(q).all())
    return ProcessInvoiceResult(invoice=invoice, lines=saved_lines, articles_upserted=upserted)


@router.post("/ingest/line", response_model=ClothesLineOut)
def ingest_line_ocr(payload: IngestLineOcr, db: Session = Depends(get_db), _: None = AuthDep):
    """Ingesta de una línea OCR (prenda) para una factura existente."""

    invoice = db.get(DataOcrInvoice, payload.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line_payload = payload.line
    line = OcrInfoClothes(invoice_id=invoice.id, **line_payload.model_dump())
    if line.reference_code and line.reference_code_origin is None:
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
    article = None
    if line.reference_code:
        q = select(ImportacionArticulosMontcau).where(
            ImportacionArticulosMontcau.reference_code == line.reference_code
        )
        article = db.scalars(q).first()
        decision = evaluate_price(line=line, article=article)
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
def list_invoice_lines(invoice_id: int, db: Session = Depends(get_db)):
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
def get_article(reference_code: str, db: Session = Depends(get_db)):
    q = select(ImportacionArticulosMontcau).where(ImportacionArticulosMontcau.reference_code == reference_code)
    article = db.scalars(q).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/process/invoice", response_model=ProcessInvoiceResult)
async def process_invoice(file: UploadFile = File(...), db: Session = Depends(get_db), _: None = AuthDep):
    """End-to-end flow:

    1) Upload invoice file
    2) OCR parse (stub for now)
    3) Save invoice to data_ocr_invoice
    4) Save detected lines to ocr_info_clothes
    5) Upsert basic articles into importacion_articulos_montcau (by reference_code)
    """

    validate_upload(file)
    file_bytes = await read_upload_limited(file, max_bytes=get_settings().max_upload_bytes)
    ocr = OcrService()
    parsed_invoice, parsed_lines = ocr.parse(file_bytes, filename=file.filename or "uploaded")
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
            invoice_file_path=stored_path,
            invoice_file_name=file.filename,
            invoice_file_mime_type=file.content_type,
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
                reference_code=ln.reference_code,
                description=ln.description,
                quantity=ln.quantity,
                price=ln.price,
                total_no_iva=ln.total_no_iva,
            )
            if line.reference_code and line.reference_code_origin is None:
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

            decision = evaluate_price(line=line, article=article)
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
    parsed_invoice, parsed_lines = ocr.parse(file_bytes, filename=file.filename or "uploaded")
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
                reference_code=ln.reference_code,
                description=ln.description,
                quantity=ln.quantity,
                price=ln.price,
                total_no_iva=ln.total_no_iva,
            )
            if line.reference_code and line.reference_code_origin is None:
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

            decision = evaluate_price(line=line, article=article)
            apply_price_decision(line, decision)
            if decision.flag:
                logger.info("price_flag", extra={"flag": decision.flag, "reference_code": line.reference_code})

    db.refresh(invoice)

    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice.id).order_by(OcrInfoClothes.id)
    saved_lines = list(db.scalars(q).all())

    return ProcessInvoiceResult(invoice=invoice, lines=saved_lines, articles_upserted=upserted)
