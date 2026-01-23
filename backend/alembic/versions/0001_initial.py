"""Initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-23

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "data_ocr_invoice",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("cif_supplier", sa.String(length=32), nullable=False),
        sa.Column("name_supplier", sa.String(length=255), nullable=True),
        sa.Column("tel_number_supplier", sa.String(length=64), nullable=True),
        sa.Column("email_supplier", sa.String(length=255), nullable=True),
        sa.Column("num_invoice", sa.String(length=64), nullable=True),
        sa.Column("total_invoice_amount", sa.Float(), nullable=True),
        sa.Column("invoice_type", sa.String(length=64), nullable=True),
        sa.Column("optional_fields", sa.JSON(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("source_channel", sa.String(length=32), nullable=True),
        sa.Column("source_thread_id", sa.String(length=128), nullable=True),
        sa.Column("source_message_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=1024), nullable=True),
        sa.Column("invoice_file_path", sa.String(length=2048), nullable=True),
        sa.Column("invoice_file_name", sa.String(length=255), nullable=True),
        sa.Column("invoice_file_mime_type", sa.String(length=128), nullable=True),
        sa.Column("invoice_file_sha256", sa.String(length=64), nullable=True),
        sa.Column("invoice_file_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_data_ocr_invoice_cif_supplier", "data_ocr_invoice", ["cif_supplier"], unique=False)
    op.create_index("ix_data_ocr_invoice_num_invoice", "data_ocr_invoice", ["num_invoice"], unique=False)
    op.create_index("ix_data_ocr_invoice_source_channel", "data_ocr_invoice", ["source_channel"], unique=False)
    op.create_index("ix_data_ocr_invoice_source_thread_id", "data_ocr_invoice", ["source_thread_id"], unique=False)
    op.create_index("ix_data_ocr_invoice_source_message_id", "data_ocr_invoice", ["source_message_id"], unique=False)

    op.create_table(
        "importacion_articulos_montcau",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ean", sa.String(length=32), nullable=True),
        sa.Column("reference_code", sa.String(length=64), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("tallaje", sa.String(length=64), nullable=True),
        sa.Column("talla", sa.String(length=64), nullable=True),
        sa.Column("largo", sa.String(length=64), nullable=True),
        sa.Column("color", sa.String(length=64), nullable=True),
        sa.Column("descripcion_color", sa.String(length=255), nullable=True),
        sa.Column("almacen", sa.String(length=64), nullable=True),
        sa.Column("familia", sa.String(length=64), nullable=True),
        sa.Column("descripcion_familia", sa.String(length=255), nullable=True),
        sa.Column("subfamilia", sa.String(length=64), nullable=True),
        sa.Column("descripcion_subfamilia", sa.String(length=255), nullable=True),
        sa.Column("marca", sa.String(length=64), nullable=True),
        sa.Column("descripcion_marca", sa.String(length=255), nullable=True),
        sa.Column("temporada", sa.String(length=64), nullable=True),
        sa.Column("descripcion_temporada", sa.String(length=255), nullable=True),
        sa.Column("modelo", sa.String(length=64), nullable=True),
        sa.Column("descripcion_modelo", sa.String(length=255), nullable=True),
        sa.Column("genero", sa.String(length=64), nullable=True),
        sa.Column("descripcion_genero", sa.String(length=255), nullable=True),
        sa.Column("material", sa.String(length=64), nullable=True),
        sa.Column("descripcion_material", sa.String(length=255), nullable=True),
        sa.Column("cantidad", sa.Integer(), nullable=True),
        sa.Column("coste_unitario", sa.Float(), nullable=True),
        sa.Column("pvp_unitario", sa.Float(), nullable=True),
        sa.Column("pvp_outlet", sa.Float(), nullable=True),
        sa.Column("foto_portada", sa.String(length=2048), nullable=True),
        sa.Column("segunda_foto", sa.String(length=2048), nullable=True),
        sa.Column("tercera_foto", sa.String(length=2048), nullable=True),
        sa.Column("cuarta_foto", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("reference_code", name="uq_reference_code"),
    )
    op.create_index(
        "ix_importacion_articulos_montcau_ean", "importacion_articulos_montcau", ["ean"], unique=False
    )
    op.create_index(
        "ix_importacion_articulos_montcau_reference_code",
        "importacion_articulos_montcau",
        ["reference_code"],
        unique=False,
    )

    op.create_table(
        "ocr_info_clothes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("data_ocr_invoice.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cif_supplier", sa.String(length=32), nullable=False),
        sa.Column("name_supplier", sa.String(length=255), nullable=True),
        sa.Column("num_invoice", sa.String(length=64), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("reference_code_raw", sa.String(length=64), nullable=True),
        sa.Column("reference_code", sa.String(length=64), nullable=True),
        sa.Column("reference_code_origin", sa.String(length=16), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("total_no_iva", sa.Float(), nullable=True),
        sa.Column("price_flag", sa.String(length=32), nullable=True),
        sa.Column("price_flag_reason", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("invoice_id", "reference_code", name="uq_invoice_reference"),
    )
    op.create_index("ix_ocr_info_clothes_invoice_id", "ocr_info_clothes", ["invoice_id"], unique=False)
    op.create_index("ix_ocr_info_clothes_cif_supplier", "ocr_info_clothes", ["cif_supplier"], unique=False)
    op.create_index("ix_ocr_info_clothes_num_invoice", "ocr_info_clothes", ["num_invoice"], unique=False)
    op.create_index("ix_ocr_info_clothes_reference_code_raw", "ocr_info_clothes", ["reference_code_raw"], unique=False)
    op.create_index("ix_ocr_info_clothes_reference_code", "ocr_info_clothes", ["reference_code"], unique=False)

    op.create_table(
        "price_observation",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("cif_supplier", sa.String(length=32), nullable=False),
        sa.Column("reference_code", sa.String(length=64), nullable=False),
        sa.Column("observed_price", sa.Float(), nullable=False),
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("data_ocr_invoice.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "line_id",
            sa.Integer(),
            sa.ForeignKey("ocr_info_clothes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("invoice_id", "line_id", name="uq_price_obs_invoice_line"),
    )
    op.create_index(
        "ix_price_observation_cif_supplier", "price_observation", ["cif_supplier"], unique=False
    )
    op.create_index(
        "ix_price_observation_reference_code", "price_observation", ["reference_code"], unique=False
    )
    op.create_index("ix_price_observation_invoice_id", "price_observation", ["invoice_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_price_observation_invoice_id", table_name="price_observation")
    op.drop_index("ix_price_observation_reference_code", table_name="price_observation")
    op.drop_index("ix_price_observation_cif_supplier", table_name="price_observation")
    op.drop_table("price_observation")

    op.drop_index("ix_ocr_info_clothes_reference_code", table_name="ocr_info_clothes")
    op.drop_index("ix_ocr_info_clothes_reference_code_raw", table_name="ocr_info_clothes")
    op.drop_index("ix_ocr_info_clothes_num_invoice", table_name="ocr_info_clothes")
    op.drop_index("ix_ocr_info_clothes_cif_supplier", table_name="ocr_info_clothes")
    op.drop_index("ix_ocr_info_clothes_invoice_id", table_name="ocr_info_clothes")
    op.drop_table("ocr_info_clothes")

    op.drop_index("ix_importacion_articulos_montcau_reference_code", table_name="importacion_articulos_montcau")
    op.drop_index("ix_importacion_articulos_montcau_ean", table_name="importacion_articulos_montcau")
    op.drop_table("importacion_articulos_montcau")

    op.drop_index("ix_data_ocr_invoice_source_message_id", table_name="data_ocr_invoice")
    op.drop_index("ix_data_ocr_invoice_source_thread_id", table_name="data_ocr_invoice")
    op.drop_index("ix_data_ocr_invoice_source_channel", table_name="data_ocr_invoice")
    op.drop_index("ix_data_ocr_invoice_num_invoice", table_name="data_ocr_invoice")
    op.drop_index("ix_data_ocr_invoice_cif_supplier", table_name="data_ocr_invoice")
    op.drop_table("data_ocr_invoice")
