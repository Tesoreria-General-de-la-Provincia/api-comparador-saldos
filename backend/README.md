# API Comparador de Saldos TGP

API REST desarrollada en FastAPI para comparar saldos bancarios entre diferentes años a partir de archivos CSV.

## 📋 Características

- ✅ Compara 2 archivos CSV de diferentes años
- ✅ Genera 2 archivos Excel:
  - `comparacion_completa.xlsx`: Todas las diferencias (NUEVAS, EXISTENTES, ELIMINADAS)
  - `comparacion_existentes.xlsx`: Solo cuentas EXISTENTES con diferencias
- ✅ Identifica automáticamente los años desde los nombres de archivo
- ✅ Maneja encoding latino (ñ, tildes, etc.)
- ✅ Números con formato latino (coma como decimal)
- ✅ Documentación interactiva con Swagger UI
- ✅ API REST totalmente asíncrona

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd API-COMPARADOR-SALDOS-TGP
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Ejecución

### Modo Desarrollo (con hot-reload)

```bash
uvicorn main:app --reload --port 8000
```

### Modo Producción

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Usando Python directamente

```bash
python main.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

Una vez iniciada la API, accede a:

- **Swagger UI (interactiva)**: http://localhost:8000/docs
- **ReDoc (alternativa)**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## 🔧 Uso de la API

### Endpoint Principal: POST /api/compare

Compara dos archivos CSV y devuelve en la respuesta JSON ambos archivos Excel codificados en base64.

#### Formato de respuesta

La respuesta será JSON con la estructura:

```json
{
  "year1": "2025",
  "year2": "2026",
  "files": [
    {
      "name": "comparacion_completa_2025_2026.xlsx",
      "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "content_base64": "UEsDB..."
    },
    {
      "name": "comparacion_existentes_2025_2026.xlsx",
      "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "content_base64": "UEsDB..."
    }
  ]
}
```

#### Usando cURL

```bash
curl -X POST "http://localhost:8000/api/compare" \
  -F "file_year1=@csv/2025.CSV" \
  -F "file_year2=@csv/2026.CSV" \
  -o response.json
```

Luego decodifica los archivos base64 con la herramienta de tu preferencia.

#### Usando Python (requests)

```python
import requests, base64

url = "http://localhost:8000/api/compare"
with open('csv/2025.CSV', 'rb') as f1, open('csv/2026.CSV', 'rb') as f2:
    files = {'file_year1': f1, 'file_year2': f2}
    response = requests.post(url, files=files)
    data = response.json()
    for f in data['files']:
        with open(f['name'], 'wb') as out:
            out.write(base64.b64decode(f['content_base64']))
```

#### Usando JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('file_year1', fileInput1.files[0]);
formData.append('file_year2', fileInput2.files[0]);

fetch('http://localhost:8000/api/compare', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(json => {
    // json.files contiene los archivos codificados en base64
});
```

## 📄 Formato de Archivos

### CSV de Entrada

Los archivos CSV deben cumplir con:

- **Separador**: Tabulación (`\t`)
- **Encoding**: `latin1` (ISO-8859-1)
- **Formato de números**: Coma como separador decimal (ej: `1.234,56`)
- **Nombre**: Debe contener el año de 4 dígitos (ej: `2025.CSV`, `saldos_2026.csv`)
- **Columnas requeridas**: Las especificadas en `data.json`

**Columnas mínimas requeridas:**
- `COD_CTA_FMT` (clave primaria)
- `SALDO_INI`
- `SALDOFIN_CALC`
- Y las definidas en `data.json`

### Excel de Salida

El ZIP generado contiene dos archivos:

#### 1. comparacion_completa.xlsx

Incluye **todas** las cuentas con diferencia:
- **NUEVAS**: Cuentas que solo existen en el año más reciente
- **EXISTENTES**: Cuentas que existen en ambos años y tienen diferencia
- **ELIMINADAS**: Cuentas que solo existen en el año anterior

#### 2. comparacion_existentes.xlsx

Incluye **solo** cuentas EXISTENTES con diferencia.

**Columnas en ambos archivos:**

| Columna | Descripción |
|---------|-------------|
| `COD_CTA_FMT` | Código único de cuenta |
| `COD_BANCO` | Código del banco |
| `DESCRIP_BCO` | Descripción del banco |
| `TIP_CTA` | Tipo de cuenta |
| `DESCRIP_TIP_CTA` | Descripción del tipo |
| `MEDIO_PAGO` | Medio de pago |
| `DESCRIP_MEDIO_PGO` | Descripción del medio |
| `NOM_CTA` | Nombre de la cuenta |
| `INGRESOS` | Ingresos |
| `EGRESOS` | Egresos |
| `SALDO_INI` | Saldo inicial |
| `CORRENT` | Corriente |
| `DESCRIP_ENTIDAD` | Descripción de la entidad |
| `CLASE_CTA` | Clase de cuenta |
| `CUENTA_FONDO` | Cuenta de fondo |
| `SECTOR` | Sector |
| `DESCRIP_SECTOR` | Descripción del sector |
| `COD_CTA_SAFYC` | Código SAFyC |
| `SALDOFIN_2025` | Saldo final del año anterior |
| `SALDO_INI_2026` | Saldo inicial del año actual |
| `DIFERENCIA` | Diferencia calculada |
| `ESTADO_CUENTA` | Estado: NUEVA, EXISTENTE o ELIMINADA |

## 🧮 Lógica de Comparación

### Estados de Cuenta

| Estado | Condición | SALDOFIN (año anterior) | SALDO_INI (año actual) | DIFERENCIA |
|--------|-----------|------------------------|------------------------|------------|
| **NUEVA** | Solo existe en año 2 | `NaN` (vacío) | Valor real | `NaN` |
| **EXISTENTE** | Existe en ambos años | Valor real | Valor real | Calculado |
| **ELIMINADA** | Solo existe en año 1 | Valor real | `NaN` (vacío) | `NaN` |

### Cálculo de Diferencia

```
DIFERENCIA = SALDO_INI_2026 - SALDOFIN_2025
```

- Para cuentas **EXISTENTES**: Se calcula normalmente
- Para cuentas **NUEVAS** o **ELIMINADAS**: Resulta en `NaN` (celda vacía en Excel)

### Filtros Aplicados

- **comparacion_completa.xlsx**: Incluye registros donde `DIFERENCIA != 0` OR `DIFERENCIA es NaN`
- **comparacion_existentes.xlsx**: Incluye registros donde `DIFERENCIA != 0` AND `ESTADO_CUENTA == "EXISTENTE"`

## 🏗️ Estructura del Proyecto

```
API-COMPARADOR-SALDOS-TGP/
├── main.py                          # Punto de entrada FastAPI
├── requirements.txt                 # Dependencias
├── data.json                        # Configuración de columnas
├── README.md                        # Este archivo
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py             # Endpoints REST
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── comparison_service.py    # Lógica de comparación
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── csv_reader.py            # Lectura de CSV
│   │   ├── excel_writer.py          # Generación de Excel
│   │   └── file_utils.py            # Utilidades generales
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Modelos Pydantic
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py              # Configuración
│
├── csv/                             # CSV de ejemplo
│   ├── 2025.CSV
│   └── 2026.CSV
│
└── target/                          # Excel de referencia
    ├── comparacion_saldos_distintos.xlsx
    └── saldos_distintos_revisado.xlsx
```

## ⚙️ Configuración

El archivo `data.json` contiene la configuración de columnas:

```json
{
  "COLUMNS_CSV": [
    "COD_BANCO", "DESCRIP_BCO", "TIP_CTA", "DESCRIP_TIP_CTA",
    "MEDIO_PAGO", "DESCRIP_MEDIO_PGO", "COD_CTA_SAFYC",
    "NOM_CTA", "SALDO_INI", "CORRENT",
    "DESCRIP_ENTIDAD", "CLASE_CTA", "CUENTA_FONDO", "SECTOR",
    "DESCRIP_SECTOR", "COD_CTA_FMT", "SALDOFIN_CALC"
  ],
  "PK_COL": "COD_CTA_FMT"
}
```

## 🐛 Solución de Problemas

### Error: "No se pudo extraer el año del nombre de archivo"

**Causa**: El nombre del archivo no contiene 4 dígitos consecutivos.

**Solución**: Renombra el archivo para incluir el año (ej: `2025.CSV`, `datos_2026.csv`)

### Error: "Error de encoding"

**Causa**: El archivo no está en formato `latin1`.

**Solución**: Guarda el archivo CSV con encoding `ISO-8859-1` o `Latin-1`.

### Error: "Faltan columnas requeridas"

**Causa**: El CSV no contiene todas las columnas necesarias.

**Solución**: Verifica que el CSV tenga al menos:
- `COD_CTA_FMT`
- `SALDO_INI`
- `SALDOFIN_CALC`

### No se genera el ZIP

**Causa**: Error durante el procesamiento.

**Solución**: 
1. Revisa los logs del servidor
2. Verifica que los CSV sean válidos
3. Intenta con los archivos de ejemplo primero

## 📊 Ejemplos de Uso

### Ejemplo 1: Comparar años 2025 y 2026

```bash
curl -X POST "http://localhost:8000/api/compare" \
  -F "file_year1=@csv/2025.CSV" \
  -F "file_year2=@csv/2026.CSV" \
  -o comparacion_2025_2026.zip
```

### Ejemplo 2: Verificar salud de la API

```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "API Comparador de Saldos TGP"
}
```

## 🔒 Seguridad

### Consideraciones

- La API acepta peticiones desde cualquier origen (CORS `*`)
- **En producción**, configurar orígenes permitidos específicos
- No hay autenticación implementada
- Los archivos se procesan en memoria y no se guardan en disco

### Recomendaciones para Producción

1. **Habilitar HTTPS**
2. **Configurar CORS** con orígenes específicos
3. **Agregar autenticación** (JWT, API Key, etc.)
4. **Limitar tamaño de archivos**
5. **Implementar rate limiting**
6. **Agregar validaciones adicionales**

## 📝 Dependencias

```
fastapi==0.109.0          # Framework web
uvicorn[standard]==0.27.0 # Servidor ASGI
python-multipart==0.0.6   # Manejo de archivos
pandas==2.1.4             # Procesamiento de datos
openpyxl==3.1.2           # Generación de Excel
numpy==1.26.3             # Operaciones numéricas
```

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Crear un branch para la nueva funcionalidad
2. Realizar los cambios
3. Asegurar que las pruebas pasen
4. Crear un Pull Request

## 📄 Licencia

Propietario - Tesorería General de la Provincia

## 📧 Contacto

Para soporte o consultas, contactar al equipo de desarrollo de TGP.

---

**Versión**: 1.0.0  
**Última actualización**: Abril 2026
