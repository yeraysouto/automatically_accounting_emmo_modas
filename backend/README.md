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

## Demo (para presentar)

Demo reproducible con `TestClient` (no necesitas levantar `uvicorn`):

```bash
cd backend
python demo/demo_flow.py
```

La demo:

- Crea un artículo maestro con `coste_unitario`
- Ingiere una factura con una línea y precio demasiado bajo
- Muestra el flag de pricing y exporta filas listas para “Importación Montcau”

## Endpoints principales

- `GET /health`
- `GET /health/db`
- `POST /process/invoice` (subir un archivo y procesarlo end-to-end)
- `POST /invoices/{id}/process` (subir nueva foto/archivo y actualizar esa factura)
- `POST /ingest/invoice` (recibir OCR ya extraído, p.ej. WhatsApp/Telegram)
- `POST /ingest/line` (recibir OCR de una prenda/línea para una factura)
- `POST /invoices/{id}/lines/{line_id}/set-reference` (completar la referencia)
- `POST /invoices` / `GET /invoices` / `GET /invoices/{id}`
- `PUT /invoices/{id}/status`
- `GET /invoices/{id}/download`
- `POST /invoices/{id}/lines` / `GET /invoices/{id}/lines`
- `PUT /articles` / `GET /articles/{reference_code}`

## Config

Por defecto usa SQLite local:

- `EMMO_DATABASE_URL=sqlite:///./emmo.db`

Opciones de engine/pool (útiles para Postgres/MySQL y despliegues largos):

- `EMMO_DB_ECHO=false` (si `true`, loguea SQL)
- `EMMO_DB_POOL_PRE_PING=true` (evita conexiones muertas)
- `EMMO_DB_POOL_SIZE=5` (no aplica a SQLite)
- `EMMO_DB_MAX_OVERFLOW=10` (no aplica a SQLite)

Hay un ejemplo en [backend/.env.example](backend/.env.example).

## Postgres (recomendado si vas a escalar)

1) Levantar Postgres en local:

```bash
cd backend
docker compose up -d
```

2) Configurar la URL (ejemplo):

```bash
export EMMO_DATABASE_URL='postgresql+psycopg://emmo:emmo@localhost:5432/emmo'
```

3) Ajustar pool para despliegue con múltiples workers/procesos:

- `EMMO_DB_POOL_PRE_PING=true`
- `EMMO_DB_POOL_SIZE=5`
- `EMMO_DB_MAX_OVERFLOW=10`

Importante: si despliegas con varios workers (p.ej. `uvicorn --workers N` o Gunicorn), **cada proceso** mantiene su propio pool. En Postgres, planifica conexiones como:

$$\text{conexiones} \approx N \times (\text{POOL\_SIZE} + \text{MAX\_OVERFLOW})$$

Recomendación práctica para escalar sin matar el Postgres:

- Empieza con `EMMO_DB_POOL_SIZE=2` y `EMMO_DB_MAX_OVERFLOW=3` si vas a tener muchos pods.
- Considera PgBouncer o un pooler gestionado delante del Postgres.

Notas de escalado del MVP:

- El rate-limit in-memory no escala horizontalmente; en producción conviene moverlo al gateway/Redis.

## Migraciones (Alembic) — recomendado en Postgres

Con Postgres y escalado, evita `create_all()` al arrancar y usa migraciones versionadas.

1) Desactiva auto-create en producción:

```bash
export EMMO_DB_AUTO_CREATE=false
```

2) Aplica migraciones (en un job/init-container/step de CI/CD):

```bash
cd backend
alembic upgrade head
```

3) Cuando cambies modelos, crea una nueva revisión:

```bash
alembic revision -m "add_x"   # (si haces a mano)
```

En este repo ya existe una migración inicial en `alembic/versions/0001_initial.py`.

## Guía concreta de pool/conexiones (para escalar)

En despliegues con múltiples workers (o múltiples pods), cada proceso mantiene su propio pool.
Para dimensionar conexiones en Postgres:

$$\text{conexiones} \approx P \times W \times (\text{POOL\_SIZE} + \text{MAX\_OVERFLOW})$$

Donde:

- $P$ = número de pods/instancias del API
- $W$ = número de workers por instancia (si usas `--workers`)

Valores iniciales recomendados (con enfoque “safe-by-default”):

- Si vas a escalar a muchos pods: `EMMO_DB_POOL_SIZE=2` y `EMMO_DB_MAX_OVERFLOW=1`
- Si el Postgres está lejos o corta conexiones: `EMMO_DB_POOL_PRE_PING=true`

Ejemplos rápidos:

- 4 pods, 2 workers/pod, pool 2+1 ⇒ $4 \times 2 \times 3 = 24$ conexiones aprox.
- 10 pods, 2 workers/pod, pool 2+1 ⇒ $10 \times 2 \times 3 = 60$ conexiones aprox.

Si el cálculo te da un número alto para el `max_connections` de Postgres, prioriza:

- bajar `POOL_SIZE/MAX_OVERFLOW`
- usar un pooler tipo PgBouncer
- revisar si realmente necesitas múltiples workers por pod (a veces basta con más pods y 1 worker)

## Cómo funciona la conexión a la BBDD

La conexión se gestiona con SQLAlchemy y el patrón “engine global + SessionLocal + dependencia FastAPI”:

- Engine/SessionLocal: [app/db/session.py](app/db/session.py) crea el `engine` y `SessionLocal` en `init_engine()`.
- Configuración: [app/settings.py](app/settings.py) carga `EMMO_DATABASE_URL` y opciones del engine/pool.
- Uso en endpoints: los handlers reciben `db: Session = Depends(get_db)`.
- Ciclo de vida: `get_db()` hace `yield db` y siempre ejecuta `db.close()` al finalizar la request.

Ejemplo (Postgres): `postgresql+psycopg://user:pass@host:5432/emmo`

### .env (entornos)

- El backend carga variables desde `backend/.env` (no se versiona) y se documenta en `backend/.env.example`.
- En producción, las variables deben venir del runtime (Docker/K8s/CI) y **no** de un archivo.

### Seguridad (API key opcional)

Si configuras `EMMO_API_KEY`, entonces las rutas de escritura requieren header:

- `X-API-Key: <tu_clave>`

Si quieres desactivar esta exigencia para escritura en desarrollo:

- `EMMO_REQUIRE_API_KEY_FOR_WRITE=false`

Si quieres exigir API key también en lecturas (GET) en entornos expuestos:

- `EMMO_REQUIRE_API_KEY_FOR_READ=true`

### Ciberseguridad (cómo se protegen las APIs)

Medidas incluidas en el backend (MVP):

- **API key** (write-only por defecto, configurable para reads).
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.
- **Request ID**: se acepta/propaga `X-Request-ID` y se añade a logs.
- **Trusted hosts** (opcional): `EMMO_ENABLE_TRUSTED_HOSTS=true` + `EMMO_TRUSTED_HOSTS=...`.
- **Rate limit** simple (opcional): `EMMO_RATE_LIMIT_PER_MINUTE`.

Recomendación mínima para producción:

- TLS (HTTPS) terminando en un reverse proxy (Nginx/Traefik/API Gateway).
- Limitar origen de CORS y redes permitidas.
- Secret manager para `EMMO_API_KEY`.
- Si se escala horizontalmente, reemplazar rate-limit in-memory por Redis/gateway.

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

Además se guarda trazabilidad en BBDD:

- `invoice_file_path`, `invoice_file_name`, `invoice_file_mime_type`
- `invoice_file_sha256` (integridad)
- `invoice_file_bytes` (tamaño)

Esto permite preparar “carpetas trimestrales” rápidamente sin re-escaneo.

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

### OCR Provider con Tesseract (opcional)

El provider incluye un modo best-effort: si el archivo es una **imagen** y tienes instaladas las dependencias,
extrae `raw_text` con Tesseract.

Requisitos típicos:

- Sistema: `tesseract-ocr`
- Python: `pytesseract` y `Pillow`

Si no están instalados (o si el archivo es PDF), el provider hace fallback a stub.
Respuesta recomendada (pero tolerante):

```json
{
	"invoice": {
		"cif_supplier": "B123...",
## Glosario rápido (PK / FK)

- **PK (Primary Key)**: columna (o conjunto) que identifica un registro de forma única (p.ej. `data_ocr_invoice.id`).
- **FK (Foreign Key)**: columna que referencia una PK de otra tabla (p.ej. `ocr_info_clothes.invoice_id` apunta a `data_ocr_invoice.id`).
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

## JSON (cómo organizarlo para múltiples facturas)

Regla: **separar cabecera vs líneas**.

- `invoice`: datos comunes (proveedor, num, total, tipo, metadata)
- `lines`: array de líneas (cada prenda/artículo)

Para evitar “keys vacías” en facturas de tipos distintos:

- Guardar campos opcionales dentro de `invoice.optional_fields`.
- Indicar `invoice.invoice_type` (p.ej. `textil`, `servicios`, `suministros`).

## Reference codes (ref_code)

Para mantener consistencia y evitar colisiones entre proveedores, el backend puede **forzar un formato canónico**:

```
<SUP>_<codigo>
```

- `<SUP>`: 3 letras mayúsculas derivadas de `name_supplier`.
- `<codigo>`: el código OCR/manual (si existe). Si no existe y está activo `EMMO_AUTO_REFERENCE_CODE`, se genera `SUP_<hash64>` determinista.

Trazabilidad:

- `reference_code_raw`: lo que vino del OCR/manual.
- `reference_code`: lo canónico para búsquedas/upserts.

## Pricing (reglas matemáticas, sin IA)

Objetivo: detectar/corregir precios demasiado bajos sin depender de descripciones poco fiables.

Reglas en orden:

1) Si existe artículo maestro (`importacion_articulos_montcau.coste_unitario`):
   - Se compara `price` con `coste_unitario * EMMO_PRICE_MIN_RATIO`.

2) Si no existe coste maestro: se usa histórico por `reference_code` (tabla `price_observation`) y su mediana.

Modos:

- `EMMO_PRICE_CORRECTION_MODE=flag_only` (marca `price_flag` y no corrige)
- `EMMO_PRICE_CORRECTION_MODE=floor_to_cost`
- `EMMO_PRICE_CORRECTION_MODE=floor_to_reference_median`

## Logs y seguimiento (qué se registra y dónde)

- Por defecto: logs a stdout (apto para Docker).
- `EMMO_LOG_JSON=true` para enviar logs estructurados a ELK/Datadog/etc.
- Se incluye `request_id` (de `X-Request-ID`) para trazabilidad de extremo a extremo.

Política de fallos (MVP):

- **Fallo duro (bloquea request)**: auth (401), MIME no permitido (415), tamaño (413), conflictos de integridad (409).
- **Fallo blando (no para el sistema)**: fallo OCR externo. La factura se crea con `status=needs_review` y se rellena `last_error_*`.

## Base de datos (SQLite → Postgres)

- Dev/arranque rápido: SQLite (por defecto).
- Producción: Postgres simplemente cambiando `EMMO_DATABASE_URL`.

Nota: para Postgres necesitas un driver instalado (p.ej. `psycopg[binary]`) y un URL tipo:

`EMMO_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/emmo`

## OCR → Importación Artículos Montcau (flujo)

1) Ingesta de OCR (cabecera + líneas) en `data_ocr_invoice` + `ocr_info_clothes`.
2) Humano-in-the-loop completa referencias cuando falten: `POST /invoices/{id}/lines/{line_id}/set-reference`.
3) Exportación para importación en Montcau:

- `GET /invoices/{id}/export/importacion-montcau`

Devuelve filas JSON listas para importar (reference_code, descripcion, cantidad, coste_unitario).
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
