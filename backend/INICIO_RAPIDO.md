# 🚀 Inicio Rápido

## Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Verificar instalación
python test_api.py
```

## Ejecutar el Servidor

```bash
# Opción 1: Usando uvicorn directamente
uvicorn main:app --reload --port 8000

# Opción 2: Usando Python
python main.py
```

El servidor estará disponible en: **http://localhost:8000**

## Acceder a la Documentación

Una vez iniciado el servidor, abre tu navegador en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Probar la API

### Opción 1: Usando Swagger UI (Recomendado)

1. Abre http://localhost:8000/docs
2. Expande `POST /api/compare`
3. Click en "Try it out"
4. Selecciona los archivos CSV
5. Click en "Execute"
6. Descarga el ZIP generado

### Opción 2: Usando el script de ejemplo

```bash
# En otra terminal (con el servidor corriendo)
python ejemplo_uso_api.py
```

### Opción 3: Usando cURL

```bash
curl -X POST "http://localhost:8000/api/compare" \
  -F "file_year1=@csv/2025.CSV" \
  -F "file_year2=@csv/2026.CSV" \
  -o resultado.zip
```

## Estructura de Archivos Generados

El ZIP contendrá:
- **comparacion_completa.xlsx**: Todas las diferencias (NUEVAS, EXISTENTES, ELIMINADAS)
- **comparacion_existentes.xlsx**: Solo cuentas EXISTENTES con diferencias

## Solución de Problemas

### El servidor no inicia

```bash
# Verificar que las dependencias estén instaladas
pip list | findstr fastapi

# Reinstalar si es necesario
pip install -r requirements.txt
```

### Error "Address already in use"

El puerto 8000 ya está en uso. Usa otro puerto:

```bash
uvicorn main:app --reload --port 8001
```

### Error al leer archivos CSV

Verifica que:
- Los archivos estén en formato CSV con separador de tabulación
- El encoding sea `latin1`
- Los nombres contengan el año (ej: 2025.CSV)

## Comandos Útiles

```bash
# Ver logs del servidor
# Los logs se muestran en la consola donde ejecutaste uvicorn

# Detener el servidor
# Presiona Ctrl+C en la terminal

# Health check
curl http://localhost:8000/health
```

## Siguiente Paso

Lee el **README.md** completo para más información sobre:
- Formato de archivos
- Lógica de comparación
- Configuración avanzada
- API Reference completo
