"""
Endpoints de la API REST para comparación de saldos.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
from io import BytesIO
import base64

from app.utils.csv_reader import read_csv_file
from app.services.comparison_service import compare_dataframes, get_comparison_summary
from app.utils.excel_writer import create_comparison_excels

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()


@router.post(
    "/compare",
    summary="Compara dos archivos CSV de diferentes años",
    description="Recibe dos archivos CSV y retorna ambos archivos Excel en JSON codificados en base64",
)
async def compare_csv_files(
    file_year1: UploadFile = File(
        ..., description="CSV del año anterior (ej: 2025.CSV)"
    ),
    file_year2: UploadFile = File(..., description="CSV del año actual (ej: 2026.CSV)"),
):
    """
    Compara dos archivos CSV de diferentes años y genera archivos Excel con las diferencias.

    **Proceso:**
    1. Valida y lee ambos archivos CSV
    2. Extrae años de los nombres de archivo
    3. Compara los datos
    4. Genera dos archivos Excel:
       - `comparacion_completa.xlsx`: Todas las diferencias (NUEVA, EXISTENTE, ELIMINADA)
       - `comparacion_existentes.xlsx`: Solo cuentas EXISTENTES con diferencias
    5. Retorna ambos archivos como JSON (base64)

    **Parámetros:**
    - **file_year1**: Archivo CSV del año anterior
    - **file_year2**: Archivo CSV del año actual

    **Retorna:**
    - JSON con los dos archivos Excel codificados en base64

    **Códigos de estado:**
    - 200: Éxito, retorna JSON con los archivos
    - 400: Error de validación
    - 422: Error de formato
    - 500: Error interno
    """
    try:
        logger.info(
            f"Iniciando comparación: {file_year1.filename} vs {file_year2.filename}"
        )

        # PASO 1: Validar y leer archivos CSV
        try:
            logger.info(f"Leyendo archivo: {file_year1.filename}")
            df1, year1 = await read_csv_file(file_year1)

            logger.info(f"Leyendo archivo: {file_year2.filename}")
            df2, year2 = await read_csv_file(file_year2)

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Error de validación: {str(e)}"
            )
        except KeyError as e:
            logger.error(f"Error de columnas faltantes: {str(e)}")
            raise HTTPException(
                status_code=422, detail=f"Error de estructura: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error al leer CSV: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=422, detail=f"Error al procesar archivos CSV: {str(e)}"
            )

        # PASO 2: Validar años (opcional: advertir si year2 no es mayor que year1)
        try:
            if int(year2) <= int(year1):
                logger.warning(
                    f"Advertencia: El año 2 ({year2}) no es posterior al año 1 ({year1})"
                )
        except ValueError:
            pass  # No es crítico si no se pueden convertir a int

        logger.info(f"Años detectados: {year1} y {year2}")
        logger.info(f"Registros en {year1}: {len(df1)}")
        logger.info(f"Registros en {year2}: {len(df2)}")

        # PASO 3: Comparar DataFrames
        try:
            logger.info("Iniciando comparación de datos...")
            df_completa, df_existentes = compare_dataframes(df1, df2, year1, year2)

            logger.info(f"Comparación completada:")
            logger.info(f"  - Registros en completa: {len(df_completa)}")
            logger.info(f"  - Registros en existentes: {len(df_existentes)}")

        except Exception as e:
            logger.error(f"Error en la comparación: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error al comparar los datos: {str(e)}"
            )

        # PASO 4: Generar archivos Excel
        try:
            logger.info("Generando archivos Excel...")
            excel_completa, excel_existentes = create_comparison_excels(
                df_completa, df_existentes
            )
            logger.info("Archivos Excel generados exitosamente")

        except Exception as e:
            logger.error(f"Error al generar Excel: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error al generar archivos Excel: {str(e)}"
            )

        # PASO 5: Preparar respuesta con ambos archivos en base64 (sin ZIP)
        try:
            logger.info("Preparando respuesta con ambos archivos Excel (base64)...")

            file1_name = f"comparacion_completa_{year1}_{year2}.xlsx"
            file2_name = f"comparacion_existentes_{year1}_{year2}.xlsx"

            resp = {
                "year1": year1,
                "year2": year2,
                "files": [
                    {
                        "name": file1_name,
                        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "content_base64": base64.b64encode(excel_completa).decode("ascii"),
                    },
                    {
                        "name": file2_name,
                        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "content_base64": base64.b64encode(excel_existentes).decode("ascii"),
                    },
                ],
            }

        except Exception as e:
            logger.error(f"Error al preparar respuesta: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error al preparar archivos: {str(e)}"
            )

        # PASO 6: Generar resumen (opcional, para logs)
        try:
            summary = get_comparison_summary(df_completa, df_existentes)
            logger.info(f"Resumen de comparación: {summary}")
        except Exception as e:
            logger.warning(f"No se pudo generar resumen: {str(e)}")

        # PASO 7: Retornar JSON con los dos archivos codificados en base64
        return JSONResponse(content=resp)

    except HTTPException:
        # Re-lanzar HTTPExceptions tal cual
        raise

    except Exception as e:
        # Capturar cualquier otro error inesperado
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check del servicio",
    description="Verifica que el servicio esté funcionando correctamente",
)
async def health_check():
    """
    Endpoint de health check.

    Retorna el estado del servicio y versión.

    **Retorna:**
    - JSON con status y version
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "API Comparador de Saldos TGP",
    }


@router.get(
    "/",
    summary="Información básica de la API",
    description="Retorna información sobre la API y link a documentación",
)
async def root():
    """
    Endpoint raíz con información básica.

    **Retorna:**
    - JSON con información de la API
    """
    return {
        "message": "API Comparador de Saldos TGP",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {"compare": "POST /api/compare - Compara dos archivos CSV"},
    }
