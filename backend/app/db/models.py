from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DataOcrInvoice(Base):
    __tablename__ = "data_ocr_invoice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cif_supplier: Mapped[str] = mapped_column(String(32), index=True)
    name_supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tel_number_supplier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    email_supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    num_invoice: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    total_invoice_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    invoice_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    optional_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Ingestion metadata (WhatsApp/Telegram/etc.)
    source_channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    source_thread_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    source_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    invoice_file_path: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    invoice_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_file_mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    clothes_lines: Mapped[list[OcrInfoClothes]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OcrInfoClothes(Base):
    __tablename__ = "ocr_info_clothes"
    __table_args__ = (
        UniqueConstraint("invoice_id", "reference_code", name="uq_invoice_reference"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    invoice_id: Mapped[int] = mapped_column(ForeignKey("data_ocr_invoice.id", ondelete="CASCADE"))

    cif_supplier: Mapped[str] = mapped_column(String(32), index=True)
    name_supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    num_invoice: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Can be null when OCR doesn't provide the reference; it can be filled later.
    reference_code: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    reference_code_origin: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_no_iva: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_flag: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    price_flag_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    invoice: Mapped[DataOcrInvoice] = relationship(back_populates="clothes_lines")


class ImportacionArticulosMontcau(Base):
    __tablename__ = "importacion_articulos_montcau"
    __table_args__ = (
        UniqueConstraint("reference_code", name="uq_reference_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # From schema image
    ean: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    reference_code: Mapped[str] = mapped_column(String(64), index=True)

    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tallaje: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    talla: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    largo: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    descripcion_color: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    almacen: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    familia: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_familia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subfamilia: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_subfamilia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marca: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_marca: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    temporada: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_temporada: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    modelo: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_modelo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    genero: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_genero: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    descripcion_material: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    cantidad: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    coste_unitario: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pvp_unitario: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pvp_outlet: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    foto_portada: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    segunda_foto: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    tercera_foto: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    cuarta_foto: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
