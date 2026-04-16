"""
API Comparador de Saldos TGP
Aplicación FastAPI para comparar saldos bancarios entre diferentes años.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
import logging
from scalar_fastapi import get_scalar_api_reference

from app.api.endpoints import router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="API Comparador de Saldos TGP",
    description="""
    API REST para comparar saldos bancarios entre diferentes años.
    
    ## Funcionalidades
    
    * **Comparación de CSV**: Compara dos archivos CSV de diferentes años
    * **Generación de Excel**: Genera reportes en formato Excel
    * **Clasificación de cuentas**: Identifica cuentas NUEVAS, EXISTENTES y ELIMINADAS
    * **Cálculo de diferencias**: Calcula diferencias de saldo automáticamente
    
    ## Uso
    
    1. Prepara dos archivos CSV con formato de tabulación
    2. Los nombres deben contener el año (ej: 2025.CSV, 2026.CSV)
    3. Envía ambos archivos al endpoint `/api/compare`
    4. Descarga el ZIP con los archivos Excel generados
    
    ## Archivos generados
    
    * **comparacion_completa.xlsx**: Todas las cuentas con diferencia
    * **comparacion_existentes.xlsx**: Solo cuentas existentes con diferencia
    
    """,
    version="1.0.0",
    contact={
        "name": "Tesorería General de la Provincia",
    },
    license_info={
        "name": "Propietario",
    },
)

# Configurar CORS para permitir peticiones desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Sin credenciales, '*' es válido y habilita CORS abierto.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router con prefijo /api
app.include_router(router, prefix="/api", tags=["Comparación de Saldos"])


# Endpoint raíz - redirige a documentación
@app.get("/", include_in_schema=False)
async def root():
    """
    Redirige a la documentación Swagger UI.
    """
    return RedirectResponse(url="/docs")


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """
    Documentación alternativa con Scalar.
    """
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check de la aplicación.

    Retorna el estado del servicio.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "API Comparador de Saldos TGP",
    }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """
    Evento ejecutado al iniciar la aplicación.
    """
    logger.info("=" * 60)
    logger.info("API Comparador de Saldos TGP - Iniciando")
    logger.info("Versión: 1.0.0")
    logger.info("=" * 60)

    # Verificar que data.json existe
    try:
        from app.config.settings import settings

        config = settings.load_config()
        logger.info(
            f"Configuración cargada: {len(config.get('COLUMNS_CSV', []))} columnas definidas"
        )
        logger.info(f"Columna PK: {config.get('PK_COL', 'N/A')}")
    except Exception as e:
        logger.error(f"Error al cargar configuración: {e}")
        logger.warning("La aplicación puede no funcionar correctamente sin data.json")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento ejecutado al cerrar la aplicación.
    """
    logger.info("=" * 60)
    logger.info("API Comparador de Saldos TGP - Cerrando")
    logger.info("=" * 60)


# Manejo global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Manejador global de excepciones no capturadas.
    """
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "type": type(exc).__name__},
    )


if __name__ == "__main__":
    import uvicorn

    # Ejecutar servidor de desarrollo
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload en desarrollo
        log_level="info",
    )
