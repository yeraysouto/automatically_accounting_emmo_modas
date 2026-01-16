# Backend (FastAPI)

API mínima para el flujo del diagrama:

- `data_ocr_invoice` (cabecera factura)
- `ocr_info_clothes` (líneas detectadas)
- `importacion_articulos_montcau` (maestro artículos / importación)

> Nota: el OCR está como **stub**. La API ya funciona y guarda datos; después conectamos el proveedor OCR real.

## Ejecutar

Desde `automatically_accounting_emmo_modas/backend`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Docs interactiva:

- http://localhost:8000/docs

## Endpoints principales

- `GET /health`
- `POST /process/invoice` (subir un archivo y procesarlo end-to-end)
- `POST /invoices` / `GET /invoices/{id}`
- `POST /invoices/{id}/lines` / `GET /invoices/{id}/lines`
- `PUT /articles` / `GET /articles/{reference_code}`

## Config

Por defecto usa SQLite local:

- `EMMA_DATABASE_URL=sqlite:///./emma.db`

Crea un `.env` opcional en `backend/.env`.
