from __future__ import annotations

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
    ProcessInvoiceResult,
)
from app.db.models import DataOcrInvoice, ImportacionArticulosMontcau, OcrInfoClothes
from app.db.session import get_db
from app.services.ocr import OcrService

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/invoices", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
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
def add_invoice_line(invoice_id: int, payload: ClothesLineCreate, db: Session = Depends(get_db)):
    invoice = db.get(DataOcrInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line = OcrInfoClothes(invoice_id=invoice_id, **payload.model_dump())
    db.add(line)
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
def upsert_article(payload: ArticleUpsert, db: Session = Depends(get_db)):
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
def process_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """End-to-end flow:

    1) Upload invoice file
    2) OCR parse (stub for now)
    3) Save invoice to data_ocr_invoice
    4) Save detected lines to ocr_info_clothes
    5) Upsert basic articles into importacion_articulos_montcau (by reference_code)
    """

    file_bytes = file.file.read()
    ocr = OcrService()
    parsed_invoice, parsed_lines = ocr.parse(file_bytes, filename=file.filename or "uploaded")

    invoice = DataOcrInvoice(
        cif_supplier=parsed_invoice.cif_supplier,
        name_supplier=parsed_invoice.name_supplier,
        tel_number_supplier=parsed_invoice.tel_number_supplier,
        email_supplier=parsed_invoice.email_supplier,
        num_invoice=parsed_invoice.num_invoice,
        total_supplier=parsed_invoice.total_supplier,
        raw_text=parsed_invoice.raw_text,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

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
        db.add(line)
        out_lines.append(line)

    db.commit()

    # Upsert minimal articles (reference_code + description + quantity/cost)
    upserted = 0
    for line in out_lines:
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

    db.commit()
    db.refresh(invoice)

    q = select(OcrInfoClothes).where(OcrInfoClothes.invoice_id == invoice.id).order_by(OcrInfoClothes.id)
    saved_lines = list(db.scalars(q).all())

    return ProcessInvoiceResult(
        invoice=invoice,
        lines=saved_lines,
        articles_upserted=upserted,
    )
