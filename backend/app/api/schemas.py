from __future__ import annotations

"""Pydantic schemas (request/response models).

These models define the public API contract.

Guidelines used in this file:
- `*Create` models represent inbound payloads.
- `*Out` models represent responses (ORM-backed via `from_attributes`).
- OCR ingest payloads (`Ingest*`) carry source metadata + extracted fields.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    """Payload to create an invoice header manually (without file/OCR)."""
    cif_supplier: str = Field(min_length=3, max_length=32)
    name_supplier: Optional[str] = None
    tel_number_supplier: Optional[str] = None
    email_supplier: Optional[str] = None
    num_invoice: Optional[str] = None
    total_invoice_amount: Optional[float] = None
    invoice_type: Optional[str] = None
    optional_fields: Optional[dict] = None
    raw_text: Optional[str] = None


class InvoiceOut(BaseModel):
    """Invoice response model (includes file metadata and status)."""
    id: int
    cif_supplier: str
    name_supplier: Optional[str]
    tel_number_supplier: Optional[str]
    email_supplier: Optional[str]
    num_invoice: Optional[str]
    total_invoice_amount: Optional[float]
    invoice_type: Optional[str]
    optional_fields: Optional[dict]
    raw_text: Optional[str]
    status: str
    last_error_code: Optional[str]
    last_error_message: Optional[str]
    invoice_file_path: Optional[str]
    invoice_file_name: Optional[str]
    invoice_file_mime_type: Optional[str]
    invoice_file_sha256: Optional[str]
    invoice_file_bytes: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceStatusUpdate(BaseModel):
    """Update an invoice workflow status.

    `clear_error=true` clears `last_error_*` fields.
    """
    status: str = Field(min_length=1, max_length=32)
    clear_error: bool = False


class ClothesLineCreate(BaseModel):
    """Payload to add a line item to an invoice."""
    cif_supplier: str = Field(min_length=3, max_length=32)
    name_supplier: Optional[str] = None
    num_invoice: Optional[str] = None
    date: Optional[date] = None

    reference_code: Optional[str] = Field(default=None, min_length=1, max_length=64)
    description: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    price: Optional[float] = Field(default=None, ge=0)
    total_no_iva: Optional[float] = Field(default=None, ge=0)


class ClothesLineOut(BaseModel):
    """Invoice line response model.

    Includes reference code normalization traceability (`reference_code_raw` and
    `reference_code_origin`) plus pricing flags.
    """
    id: int
    invoice_id: int
    cif_supplier: str
    name_supplier: Optional[str]
    num_invoice: Optional[str]
    date: Optional[date]

    reference_code_raw: Optional[str]
    reference_code: Optional[str]
    reference_code_origin: Optional[str]
    description: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    total_no_iva: Optional[float]
    price_flag: Optional[str]
    price_flag_reason: Optional[str]

    model_config = {"from_attributes": True}


class ArticleUpsert(BaseModel):
    """Payload to upsert a Montcau article master row.

    The API typically upserts a minimal subset initially, then enriches later.
    """
    ean: Optional[str] = None
    reference_code: str = Field(min_length=1, max_length=64)

    descripcion: Optional[str] = None
    tallaje: Optional[str] = None
    talla: Optional[str] = None
    largo: Optional[str] = None
    color: Optional[str] = None

    descripcion_color: Optional[str] = None
    almacen: Optional[str] = None
    familia: Optional[str] = None
    descripcion_familia: Optional[str] = None
    subfamilia: Optional[str] = None
    descripcion_subfamilia: Optional[str] = None
    marca: Optional[str] = None
    descripcion_marca: Optional[str] = None
    temporada: Optional[str] = None
    descripcion_temporada: Optional[str] = None
    modelo: Optional[str] = None
    descripcion_modelo: Optional[str] = None
    genero: Optional[str] = None
    descripcion_genero: Optional[str] = None
    material: Optional[str] = None
    descripcion_material: Optional[str] = None

    cantidad: Optional[int] = Field(default=None, ge=0)
    coste_unitario: Optional[float] = Field(default=None, ge=0)
    pvp_unitario: Optional[float] = Field(default=None, ge=0)
    pvp_outlet: Optional[float] = Field(default=None, ge=0)

    foto_portada: Optional[str] = None
    segunda_foto: Optional[str] = None
    tercera_foto: Optional[str] = None
    cuarta_foto: Optional[str] = None


class ArticleOut(BaseModel):
    """Article response model (ORM-backed)."""
    id: int
    ean: Optional[str]
    reference_code: str

    descripcion: Optional[str]
    tallaje: Optional[str]
    talla: Optional[str]
    largo: Optional[str]
    color: Optional[str]

    descripcion_color: Optional[str]
    almacen: Optional[str]
    familia: Optional[str]
    descripcion_familia: Optional[str]
    subfamilia: Optional[str]
    descripcion_subfamilia: Optional[str]
    marca: Optional[str]
    descripcion_marca: Optional[str]
    temporada: Optional[str]
    descripcion_temporada: Optional[str]
    modelo: Optional[str]
    descripcion_modelo: Optional[str]
    genero: Optional[str]
    descripcion_genero: Optional[str]
    material: Optional[str]
    descripcion_material: Optional[str]

    cantidad: Optional[int]
    coste_unitario: Optional[float]
    pvp_unitario: Optional[float]
    pvp_outlet: Optional[float]

    foto_portada: Optional[str]
    segunda_foto: Optional[str]
    tercera_foto: Optional[str]
    cuarta_foto: Optional[str]

    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessInvoiceResult(BaseModel):
    """Result of an end-to-end invoice ingestion process."""
    invoice: InvoiceOut
    lines: list[ClothesLineOut]
    articles_upserted: int


class LineSetReference(BaseModel):
    """Payload to set/complete a missing reference code for an existing line."""
    reference_code: str = Field(min_length=1, max_length=64)


class IngestInvoiceOcr(BaseModel):
    """Payload for pre-parsed OCR invoice ingestion.

    Used when OCR parsing happens upstream (e.g., WhatsApp/Telegram pipeline).
    """
    # Where this came from (WhatsApp/Telegram)
    source_channel: str = Field(min_length=2, max_length=32)
    source_thread_id: Optional[str] = Field(default=None, max_length=128)
    source_message_id: Optional[str] = Field(default=None, max_length=128)

    # Invoice header OCR
    cif_supplier: str = Field(min_length=3, max_length=32)
    name_supplier: Optional[str] = None
    tel_number_supplier: Optional[str] = None
    email_supplier: Optional[str] = None
    num_invoice: Optional[str] = None
    total_invoice_amount: Optional[float] = None
    invoice_type: Optional[str] = None
    optional_fields: Optional[dict] = None
    raw_text: Optional[str] = None

    # Optional detected lines
    lines: list[ClothesLineCreate] = Field(default_factory=list)


class IngestLineOcr(BaseModel):
    """Payload for ingesting a single OCR line into an existing invoice."""
    source_channel: str = Field(min_length=2, max_length=32)
    source_thread_id: Optional[str] = Field(default=None, max_length=128)
    source_message_id: Optional[str] = Field(default=None, max_length=128)

    invoice_id: int
    line: ClothesLineCreate
