"""
Endpoints de la API REST para comparación de saldos.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import logging
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

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
    description="Recibe dos archivos CSV y genera un ZIP con dos Excel de comparación",
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
    5. Retorna un archivo ZIP con ambos Excel

    **Parámetros:**
    - **file_year1**: Archivo CSV del año anterior
    - **file_year2**: Archivo CSV del año actual

    **Retorna:**
    - Archivo ZIP conteniendo los dos archivos Excel

    **Códigos de estado:**
    - 200: Éxito, retorna ZIP
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

        # PASO 5: Crear ZIP con ambos archivos
        try:
            logger.info("Creando archivo ZIP...")
            zip_buffer = BytesIO()

            with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as zip_file:
                zip_file.writestr("comparacion_completa.xlsx", excel_completa)
                zip_file.writestr("comparacion_existentes.xlsx", excel_existentes)

            zip_buffer.seek(0)
            logger.info("Archivo ZIP creado exitosamente")

        except Exception as e:
            logger.error(f"Error al crear ZIP: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error al crear archivo ZIP: {str(e)}"
            )

        # PASO 6: Generar resumen (opcional, para logs)
        try:
            summary = get_comparison_summary(df_completa, df_existentes)
            logger.info(f"Resumen de comparación: {summary}")
        except Exception as e:
            logger.warning(f"No se pudo generar resumen: {str(e)}")

        # PASO 7: Retornar ZIP como descarga
        filename = f"comparacion_saldos_{year1}_{year2}.zip"

        return StreamingResponse(
            BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

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
