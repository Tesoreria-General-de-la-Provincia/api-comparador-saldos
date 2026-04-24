"""
Utilidades para manejo de archivos y validaciones.
"""

import re
import pandas as pd
import numpy as np


def extract_year_from_filename(filename: str) -> str:
    """
    Extrae año de 4 dígitos del nombre de archivo.

    Args:
        filename: Nombre del archivo (ej: "2025.CSV", "saldos_2026.csv")

    Returns:
        str: Año extraído (ej: "2025")

    Raises:
        ValueError: Si no se encuentra año en el nombre

    Examples:
        >>> extract_year_from_filename("2025.CSV")
        "2025"
        >>> extract_year_from_filename("saldos_2026.csv")
        "2026"
        >>> extract_year_from_filename("datos-2025-final.CSV")
        "2025"
    """
    match = re.search(r"(\d{4})", filename)
    if not match:
        raise ValueError(
            f"No se pudo extraer el año del nombre de archivo: {filename}. "
            f"El nombre debe contener 4 dígitos consecutivos (ej: 2025)."
        )
    return match.group(1)


def validate_csv_extension(filename: str) -> bool:
    """
    Valida que el archivo tenga extensión .csv o .CSV

    Args:
        filename: Nombre del archivo

    Returns:
        bool: True si es CSV, False en caso contrario

    Examples:
        >>> validate_csv_extension("data.csv")
        True
        >>> validate_csv_extension("data.CSV")
        True
        >>> validate_csv_extension("data.xlsx")
        False
    """
    return filename.lower().endswith(".csv")


def convert_numeric_string(value) -> float:
    """
    Convierte string numérico con formato latino a float.

    El formato latino usa coma como separador decimal.

    Args:
        value: Valor a convertir (str, float, int, None)

    Returns:
        float: Valor convertido, o NaN si no es convertible

    Examples:
        >>> convert_numeric_string("1.234,56")
        1234.56
        >>> convert_numeric_string("1234,56")
        1234.56
        >>> convert_numeric_string("1234")
        1234.0
        >>> convert_numeric_string("")
        nan
        >>> convert_numeric_string(None)
        nan
    """
    # Si ya es un número, retornar directamente
    if isinstance(value, (int, float)):
        return float(value)

    # Si es NaN o None o string vacío, retornar NaN
    if pd.isna(value) or value == "" or value is None:
        return np.nan

    # Convertir a string y reemplazar coma por punto
    value_str = str(value).strip()

    # Manejar caso de string vacío después del strip
    if not value_str:
        return np.nan

    # Reemplazar coma por punto para formato decimal
    value_str = value_str.replace(",", ".")

    try:
        return float(value_str)
    except (ValueError, AttributeError):
        return np.nan


def convert_dataframe_numeric_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Convierte columnas numéricas de un DataFrame usando formato latino.

    Args:
        df: DataFrame a procesar
        columns: Lista de nombres de columnas a convertir

    Returns:
        pd.DataFrame: DataFrame con columnas convertidas

    Note:
        Modifica el DataFrame in-place y también lo retorna.
    """
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_numeric_string)

    return df
