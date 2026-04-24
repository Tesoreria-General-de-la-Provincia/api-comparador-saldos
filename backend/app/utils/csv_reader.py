"""
Módulo para lectura y procesamiento de archivos CSV.
"""

import pandas as pd
from fastapi import UploadFile
from typing import Tuple
import io

from app.utils.file_utils import (
    extract_year_from_filename,
    validate_csv_extension,
    convert_dataframe_numeric_columns,
)
from app.config.settings import settings


async def read_csv_file(file: UploadFile) -> Tuple[pd.DataFrame, str]:
    """
    Lee un archivo CSV y extrae el año del nombre.

    Proceso:
    1. Valida extensión del archivo (.csv)
    2. Extrae año del nombre de archivo (4 dígitos)
    3. Lee CSV con encoding latin1 y separador de tabulación
    4. Convierte columnas numéricas (coma → punto decimal)
    5. Valida que contenga las columnas requeridas

    Args:
        file: Archivo CSV subido a través de FastAPI

    Returns:
        tuple: (DataFrame procesado, año extraído)

    Raises:
        ValueError: Si la extensión no es CSV o falta el año
        pd.errors.ParserError: Si el CSV está mal formado
        KeyError: Si faltan columnas requeridas

    Example:
        >>> file = UploadFile(filename="2025.CSV", file=...)
        >>> df, year = await read_csv_file(file)
        >>> print(year)
        "2025"
        >>> print(df.columns)
        Index(['COD_BANCO', 'DESCRIP_BCO', ...])
    """
    # 1. Validar extensión
    if not validate_csv_extension(file.filename):
        raise ValueError(
            f"El archivo '{file.filename}' no es un archivo CSV válido. "
            f"Debe tener extensión .csv o .CSV"
        )

    # 2. Extraer año del nombre
    year = extract_year_from_filename(file.filename)

    # 3. Leer contenido del archivo
    contents = await file.read()

    # 4. Leer CSV con pandas
    try:
        # Usar StringIO para leer desde bytes
        df = pd.read_csv(
            io.BytesIO(contents),
            sep="\t",
            encoding="latin1",
            dtype=str,  # Leer todo como string inicialmente
        )
    except pd.errors.ParserError as e:
        raise pd.errors.ParserError(
            f"Error al parsear el archivo CSV '{file.filename}': {str(e)}"
        )
    except UnicodeDecodeError as e:
        raise ValueError(
            f"Error de encoding en el archivo '{file.filename}'. "
            f"Se esperaba encoding latin1: {str(e)}"
        )

    # 5. Limpiar filas no deseadas (totales GRAL)
    df = remove_gral_rows(df)

    # 6. Validar que exista la columna PK
    pk_col = settings.pk_column
    if pk_col not in df.columns:
        raise KeyError(
            f"El archivo CSV no contiene la columna clave '{pk_col}'. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    # 7. Convertir columnas numéricas
    numeric_cols = settings.numeric_columns
    df = convert_dataframe_numeric_columns(df, numeric_cols)

    # 8. Validar columnas requeridas (warning si faltan, pero continuar)
    required_cols = set(settings.columns_csv + numeric_cols + [pk_col])
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        # Solo advertir, no fallar (algunas columnas pueden ser opcionales)
        print(f"Advertencia: Columnas faltantes en '{file.filename}': {missing_cols}")

    return df, year


def remove_gral_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina filas de totales/encabezados agregados al final del CSV.

    Estas filas suelen contener textos como:
    - SALDO_INI_GRAL
    - INGRESO_GRAL
    - EGRESO_GRAL
    - SALDO_FIN_GRAL
    - CF_PROVINCIA
    """
    if df.empty:
        return df

    # Normalizar a string de forma segura (evita NaN/float en búsquedas y strip)
    df_str = df.fillna("").astype(str)
    patterns = ["GRAL", "CF_PROVINCIA", "SALDO_INI_GRAL"]

    # Marcar filas que contengan cualquiera de los patrones
    mask = df_str.apply(
        lambda row: any(pat in value for pat in patterns for value in row.values),
        axis=1,
    )

    # Eliminar filas con poca información y sin COD_CTA_FMT
    pk_col = settings.pk_column
    if pk_col not in df_str.columns:
        # Si no existe PK todavía, al menos filtramos filas de totales/encabezados.
        return df[~mask].copy()

    filled_counts = df_str.apply(
        lambda row: sum(
            value.strip() != "" and value.lower() != "nan" for value in row.values
        ),
        axis=1,
    )
    missing_pk = df_str[pk_col].str.strip().eq("") | df_str[pk_col].str.lower().eq(
        "nan"
    )
    sparse_row = (filled_counts <= 5) & missing_pk

    # Filtrar esas filas
    return df[~(mask | sparse_row)].copy()


def validate_dataframe_columns(df: pd.DataFrame, filename: str) -> None:
    """
    Valida que el DataFrame contenga las columnas mínimas requeridas.

    Args:
        df: DataFrame a validar
        filename: Nombre del archivo (para mensajes de error)

    Raises:
        KeyError: Si faltan columnas críticas
    """
    # Columnas críticas que DEBEN existir
    critical_columns = [settings.pk_column, "SALDO_INI", "SALDOFIN_CALC"]

    missing_critical = set(critical_columns) - set(df.columns)

    if missing_critical:
        raise KeyError(
            f"El archivo '{filename}' no contiene columnas críticas requeridas: "
            f"{missing_critical}. Columnas encontradas: {list(df.columns)}"
        )


def check_duplicate_keys(df: pd.DataFrame, filename: str) -> None:
    """
    Verifica que no haya claves duplicadas en el DataFrame.

    Args:
        df: DataFrame a verificar
        filename: Nombre del archivo (para mensajes de error)

    Raises:
        ValueError: Si hay claves duplicadas
    """
    pk_col = settings.pk_column

    if pk_col in df.columns:
        duplicates = df[pk_col].duplicated()
        if duplicates.any():
            dup_values = df[pk_col][duplicates].unique()
            raise ValueError(
                f"El archivo '{filename}' contiene claves duplicadas en '{pk_col}': "
                f"{list(dup_values)[:5]}{'...' if len(dup_values) > 5 else ''}"
            )
