# Comparador de Saldos TGP

API REST para comparar saldos bancarios entre dos años fiscales. Recibe dos archivos CSV (uno por año), los compara y devuelve un ZIP con dos reportes Excel.

## Stack

- **Backend:** Python 3.12 · FastAPI · Pandas · Openpyxl
- **Gestor de paquetes:** `uv`
- **Contenedor:** Docker + Docker Compose

## Levantar con Docker

```bash
docker compose up --build
```

La API quedará disponible en `http://localhost:8000`.  
Documentación interactiva: `http://localhost:8000/docs`

## Levantar en local

```bash
cd backend
uv sync
.venv\Scripts\activate       # Windows
uvicorn main:app --reload
```

## Endpoint principal

**`POST /api/compare`**

| Campo | Tipo | Descripción |
| `file_year1` | file | CSV del año anterior (ej: `2025.CSV`) |
| `file_year2` | file | CSV del año actual (ej: `2026.CSV`) |

**Respuesta:** `application/zip` con dos archivos Excel:

- `comparacion_completa.xlsx` — todas las cuentas con diferencia (NUEVA / EXISTENTE / ELIMINADA)
- `comparacion_existentes.xlsx` — solo cuentas que existían en ambos años

```bash
curl -X POST http://localhost:8000/api/compare \
  -F "file_year1=@2025.CSV" \
  -F "file_year2=@2026.CSV" \
  --output comparacion.zip
```

## Formato del CSV

Archivos delimitados por tabulación (`\t`). El año se extrae automáticamente del nombre del archivo. La clave primaria es `COD_CTA_FMT`. Las columnas y la PK se configuran en `backend/data.json`.

## Importante

Cambiar la URL de la api en el frontend al levantar. NO LOCALHOST. Poner IP.
