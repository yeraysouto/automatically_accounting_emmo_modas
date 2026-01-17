from fastapi.testclient import TestClient


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_invoice_allows_line_without_reference(client: TestClient):
    payload = {
        "source_channel": "whatsapp",
        "source_thread_id": "chat-1",
        "source_message_id": "msg-1",
        "cif_supplier": "B12345678",
        "name_supplier": "Proveedor SL",
        "num_invoice": "F-1",
        "total_invoice_amount": 10.5,
        "raw_text": "OCR factura",
        "lines": [
            {
                "cif_supplier": "B12345678",
                "name_supplier": "Proveedor SL",
                "num_invoice": "F-1",
                "date": None,
                "reference_code": None,
                "description": "CAMISETA NEGRA",
                "quantity": 2,
                "price": 5.25,
                "total_no_iva": 10.5,
            }
        ],
    }

    r = client.post("/ingest/invoice", json=payload, headers={"X-API-Key": "test-key"})
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["invoice"]["id"] > 0
    assert len(data["lines"]) == 1
    assert data["lines"][0]["reference_code"] is None
    assert data["articles_upserted"] == 0


def test_set_reference_upserts_article(client: TestClient):
    # Create invoice
    inv = client.post(
        "/invoices",
        json={
            "cif_supplier": "B12345678",
            "name_supplier": "Proveedor SL",
            "num_invoice": "F-2",
        },
        headers={"X-API-Key": "test-key"},
    ).json()

    # Add line without reference
    line = client.post(
        f"/invoices/{inv['id']}/lines",
        json={
            "cif_supplier": "B12345678",
            "name_supplier": "Proveedor SL",
            "num_invoice": "F-2",
            "reference_code": None,
            "description": "PANTALON",
            "quantity": 1,
            "price": 9.99,
            "total_no_iva": 9.99,
        },
        headers={"X-API-Key": "test-key"},
    ).json()

    # Complete reference
    r = client.post(
        f"/invoices/{inv['id']}/lines/{line['id']}/set-reference",
        json={"reference_code": "ABC123"},
        headers={"X-API-Key": "test-key"},
    )
    assert r.status_code == 200, r.text

    # Article should exist
    art = client.get("/articles/ABC123")
    assert art.status_code == 200
    art_json = art.json()
    assert art_json["reference_code"] == "ABC123"
    assert art_json["descripcion"] == "PANTALON"


def test_file_upload_requires_api_key_when_configured(client: TestClient):
    # Missing key => 401
    r = client.post(
        "/process/invoice",
        files={"file": ("invoice.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    assert r.status_code == 401

    # With key => 200 (stub OCR)
    r2 = client.post(
        "/process/invoice",
        files={"file": ("invoice.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers={"X-API-Key": "test-key"},
    )
    assert r2.status_code == 200, r2.text


def test_file_upload_rejects_unsupported_mime(client: TestClient):
    r = client.post(
        "/process/invoice",
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers={"X-API-Key": "test-key"},
    )
    assert r.status_code == 415
