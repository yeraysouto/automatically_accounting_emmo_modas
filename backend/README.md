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
- `POST /invoices/{id}/process` (subir nueva foto/archivo y actualizar esa factura)
- `POST /ingest/invoice` (recibir OCR ya extraído, p.ej. WhatsApp/Telegram)
- `POST /ingest/line` (recibir OCR de una prenda/línea para una factura)
- `POST /invoices/{id}/lines/{line_id}/set-reference` (completar la referencia)
- `POST /invoices` / `GET /invoices/{id}`
- `POST /invoices/{id}/lines` / `GET /invoices/{id}/lines`
- `PUT /articles` / `GET /articles/{reference_code}`

## Config

Por defecto usa SQLite local:

- `EMMA_DATABASE_URL=sqlite:///./emma.db`

Hay un ejemplo en [backend/.env.example](backend/.env.example).

### Seguridad (API key opcional)

Si configuras `EMMA_API_KEY`, entonces las rutas que suben archivos requieren header:

- `X-API-Key: <tu_clave>`

### Límites de subida

- `EMMA_MAX_UPLOAD_BYTES` (por defecto 15MB)
- `EMMA_ALLOWED_UPLOAD_MIME_TYPES` (por defecto `image/jpeg,image/png,application/pdf`)

### OCR externo (opcional)

Si quieres que el backend se conecte a **tu OCR via API**, configura:

- `EMMA_OCR_API_URL=https://tu-ocr/endpoint`
- `EMMA_OCR_API_KEY=...` (opcional; se envía como `Authorization: Bearer <key>`)
- `EMMA_OCR_API_TIMEOUT_S=60`

El backend hace `POST multipart/form-data` con el campo `file`.

### OCR Provider local (para empezar rápido)

Puedes levantar un **OCR Provider stub** (una API separada) y apuntar el backend a ella:

1) En una terminal:

```bash
uvicorn app.ocr_provider_main:app --reload --port 8001
```

2) En `backend/.env`:

```bash
EMMA_OCR_API_URL=http://localhost:8001/ocr/invoice
```

Luego usa `POST /process/invoice` o `POST /invoices/{id}/process` en el backend (puerto 8000).

Respuesta recomendada (pero tolerante):

```json
{
	"invoice": {
		"cif_supplier": "B123...",
		"name_supplier": "Proveedor SL",
		"num_invoice": "F-2026-001",
		"date": "2026-01-16",
		"total_supplier": 123.45,
		"raw_text": "texto completo OCR (opcional)"
	},
	"lines": [
		{
			"reference_code": "ABC123",
			"description": "CAMISETA",
			"quantity": 10,
			"price": 5.5,
			"total_no_iva": 55.0
		}
	]
}
```

Crea un `.env` opcional en `backend/.env`.
