from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    cif_supplier: str = Field(min_length=3, max_length=32)
    name_supplier: Optional[str] = None
    tel_number_supplier: Optional[str] = None
    email_supplier: Optional[str] = None
    num_invoice: Optional[str] = None
    total_supplier: Optional[float] = None
    raw_text: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    cif_supplier: str
    name_supplier: Optional[str]
    tel_number_supplier: Optional[str]
    email_supplier: Optional[str]
    num_invoice: Optional[str]
    total_supplier: Optional[float]
    raw_text: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ClothesLineCreate(BaseModel):
    cif_supplier: str = Field(min_length=3, max_length=32)
    name_supplier: Optional[str] = None
    num_invoice: Optional[str] = None
    date: Optional[date] = None

    reference_code: str = Field(min_length=1, max_length=64)
    description: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    price: Optional[float] = Field(default=None, ge=0)
    total_no_iva: Optional[float] = Field(default=None, ge=0)


class ClothesLineOut(BaseModel):
    id: int
    invoice_id: int
    cif_supplier: str
    name_supplier: Optional[str]
    num_invoice: Optional[str]
    date: Optional[date]

    reference_code: str
    description: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    total_no_iva: Optional[float]

    model_config = {"from_attributes": True}


class ArticleUpsert(BaseModel):
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
    invoice: InvoiceOut
    lines: list[ClothesLineOut]
    articles_upserted: int
