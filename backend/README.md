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

- `EMMO_DATABASE_URL=sqlite:///./emmo.db`

Hay un ejemplo en [backend/.env.example](backend/.env.example).

### Seguridad (API key opcional)

Si configuras `EMMO_API_KEY`, entonces las rutas de escritura requieren header:

- `X-API-Key: <tu_clave>`

Si quieres desactivar esta exigencia para escritura en desarrollo:

- `EMMO_REQUIRE_API_KEY_FOR_WRITE=false`

### Límites de subida

- `EMMO_MAX_UPLOAD_BYTES` (por defecto 15MB)
- `EMMO_ALLOWED_UPLOAD_MIME_TYPES` (por defecto `image/jpeg,image/png,application/pdf`)

### Almacenamiento de PDFs/Imágenes

Al subir una factura por `POST /process/invoice` o `POST /invoices/{id}/process` se guarda el archivo en:

```
<storage_root>/invoices/<year>/Q<quarter>/<uuid>.<ext>
```

Configuración:

- `EMMO_STORAGE_ROOT=./storage`
- `EMMO_STORE_UPLOADS=true`

### OCR externo (opcional)

Si quieres que el backend se conecte a **tu OCR via API**, configura:

- `EMMO_OCR_API_URL=https://tu-ocr/endpoint`
- `EMMO_OCR_API_KEY=...` (opcional; se envía como `Authorization: Bearer <key>`)
- `EMMO_OCR_API_TIMEOUT_S=60`

El backend hace `POST multipart/form-data` con el campo `file`.

### Reference code (fallback opcional)

Si el OCR no aporta `reference_code`, puedes activar un fallback determinista:

- `EMMO_AUTO_REFERENCE_CODE=true`
- Formato: `AAA_<hash64>` usando el nombre del proveedor + descripción + num
to de factura.

Esto facilita trazabilidad sin bloquear el flujo. El origen queda en `reference_code_origin`.

### Pricing (reglas matemáticas, sin IA)

Se compara el precio OCR contra `coste_unitario` del maestro de artículos (si existe).

- `EMMO_PRICE_CORRECTION_MODE=flag_only` (por defecto)
- `EMMO_PRICE_CORRECTION_MODE=floor_to_cost` (corrige a coste)
- `EMMO_PRICE_MIN_RATIO=0.7` (precio mínimo relativo)

Cuando se detecta un precio bajo se marca `price_flag` y `price_flag_reason`.

### OCR Provider local (para empezar rápido)

Puedes levantar un **OCR Provider stub** (una API separada) y apuntar el backend a ella:

1) En una terminal:

```bash
uvicorn app.ocr_provider_main:app --reload --port 8001
```

2) En `backend/.env`:

```bash
EMMO_OCR_API_URL=http://localhost:8001/ocr/invoice
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
		"total_invoice_amount": 123.45,
		"invoice_type": "textil",
		"optional_fields": {"campana": "rebajas"},
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
