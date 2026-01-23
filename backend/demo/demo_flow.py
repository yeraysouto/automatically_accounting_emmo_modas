from __future__ import annotations

import os
from pprint import pprint

from fastapi.testclient import TestClient


def _bootstrap_env() -> None:
    # Minimal demo env
    os.environ.setdefault("EMMO_DATABASE_URL", "sqlite:///./demo.db")
    os.environ.setdefault("EMMO_API_KEY", "demo-key")
    os.environ.setdefault("EMMO_ENFORCE_REFERENCE_CODE_PREFIX", "true")
    os.environ.setdefault("EMMO_PRICE_CORRECTION_MODE", "flag_only")
    os.environ.setdefault("EMMO_PRICE_MIN_RATIO", "0.7")


def main() -> None:
    _bootstrap_env()

    # Import after env setup
    import app.settings as settings_module

    settings_module.get_settings.cache_clear()

    import app.db.session as session_module

    session_module.init_engine(settings_module.get_settings().database_url)

    import app.main as main_module

    app = main_module.create_app()

    with TestClient(app) as client:
        headers = {"X-API-Key": "demo-key"}

        # 1) Create a master article with a known cost (used by pricing rule)
        r = client.put(
            "/articles",
            headers=headers,
            json={
                "reference_code": "PRO_ABC123",
                "descripcion": "PANTALON",
                "coste_unitario": 10.0,
            },
        )
        r.raise_for_status()

        # 2) Ingest an invoice with one line that has a too-low price
        ingest_payload = {
            "source_channel": "whatsapp",
            "source_thread_id": "chat-demo",
            "source_message_id": "msg-demo",
            "cif_supplier": "B12345678",
            "name_supplier": "Proveedor SL",
            "num_invoice": "F-DEMO-1",
            "total_invoice_amount": 10.0,
            "invoice_type": "textil",
            "optional_fields": {"season": "rebajas"},
            "raw_text": "OCR demo",
            "lines": [
                {
                    "cif_supplier": "B12345678",
                    "name_supplier": "Proveedor SL",
                    "num_invoice": "F-DEMO-1",
                    "date": None,
                    "reference_code": "ABC123",
                    "description": "PANTALON",
                    "quantity": 1,
                    "price": 1.0,
                    "total_no_iva": 1.0,
                }
            ],
        }

        r2 = client.post("/ingest/invoice", headers=headers, json=ingest_payload)
        r2.raise_for_status()
        data = r2.json()

        print("\n=== Ingest result (invoice + lines) ===")
        pprint(data)

        invoice_id = data["invoice"]["id"]

        # 3) Export lines into Importación Artículos Montcau JSON
        r3 = client.get(f"/invoices/{invoice_id}/export/importacion-montcau", headers=headers)
        r3.raise_for_status()

        print("\n=== Export importacion-montcau ===")
        pprint(r3.json())


if __name__ == "__main__":
    main()
