# automatically_accounting_emmo_modas
macros contabilidad automatica tienda (EMMO).

## Backend (FastAPI)

Hay un backend en [backend/README.md](backend/README.md) con una API mínima para:

- Subir facturas y guardar cabecera (`data_ocr_invoice`)
- Guardar líneas (`ocr_info_clothes`)
- Upsert de artículos (`importacion_articulos_montcau`)

## Documentación (LaTeX)

Documento técnico y plan por fases en [docs/emma_system.tex](docs/emma_system.tex) (instrucciones de compilación en [docs/README.md](docs/README.md)).

## Script legado

- `automate_reading_accountant.js`: prototipo/legado usado para pruebas iniciales.
	- No es parte del backend actual.
	- No se ejecuta en producción ni lo importa el backend.
	- Se mantiene sólo como referencia histórica (se puede eliminar cuando ya no aporte valor).

## Demo

Hay una demo reproducible (sin levantar servidor) en [backend/README.md](backend/README.md).
