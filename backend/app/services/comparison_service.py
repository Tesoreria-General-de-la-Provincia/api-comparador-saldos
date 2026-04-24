"""
Servicio de comparación de saldos entre dos años.
Contiene la lógica principal del negocio.
"""

import pandas as pd
import numpy as np
from typing import Tuple

from app.config.settings import settings


def compare_dataframes(
    df_year1: pd.DataFrame, df_year2: pd.DataFrame, year1: str, year2: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compara dos DataFrames de diferentes años y genera reportes de diferencias.

    Proceso:
    1. Preparación: extraer configuración y columnas relevantes
    2. Merge FULL OUTER JOIN para capturar todos los registros
    3. Determinar estado de cada cuenta (NUEVA, EXISTENTE, ELIMINADA)
    4. Calcular valores financieros (SALDOFIN_2025, SALDO_INI_2026, DIFERENCIA)
    5. Rellenar datos base según estado
    6. Generar dos DataFrames filtrados

    Args:
        df_year1: DataFrame del año anterior (ej: 2025)
        df_year2: DataFrame del año actual (ej: 2026)
        year1: Año del primer DataFrame (string, ej: "2025")
        year2: Año del segundo DataFrame (string, ej: "2026")

    Returns:
        tuple: (df_comparacion_completa, df_comparacion_existentes)
            - df_comparacion_completa: TODAS las cuentas con diferencia != 0
            - df_comparacion_existentes: Solo EXISTENTES con diferencia != 0

    Example:
        >>> df1 = pd.read_csv('2025.CSV', sep='\\t')
        >>> df2 = pd.read_csv('2026.CSV', sep='\\t')
        >>> df_completa, df_existentes = compare_dataframes(df1, df2, "2025", "2026")
        >>> print(df_completa['ESTADO_CUENTA'].value_counts())
        EXISTENTE    17
        NUEVA        16
        ELIMINADA     5
    """
    # PASO 1: Preparación
    pk_col = settings.pk_column
    columns_csv = settings.columns_csv

    print(f"Comparando año {year1} vs {year2}")
    print(f"Registros año {year1}: {len(df_year1)}")
    print(f"Registros año {year2}: {len(df_year2)}")

    # PASO 2: Merge FULL OUTER JOIN
    # indicator=True añade columna '_merge' con: 'left_only', 'right_only', 'both'
    merged = pd.merge(
        df_year1,
        df_year2,
        on=pk_col,
        how="outer",
        suffixes=("_y1", "_y2"),
        indicator=True,
    )

    print(f"Total de cuentas después del merge: {len(merged)}")
    print(f"  - Solo en {year1}: {len(merged[merged['_merge'] == 'left_only'])}")
    print(f"  - Solo en {year2}: {len(merged[merged['_merge'] == 'right_only'])}")
    print(f"  - En ambos: {len(merged[merged['_merge'] == 'both'])}")

    # PASO 3: Determinar Estado de Cuenta
    def get_estado(merge_indicator):
        """Determina el estado según el resultado del merge"""
        if merge_indicator == "left_only":
            return "ELIMINADA"
        elif merge_indicator == "right_only":
            return "NUEVA"
        else:  # 'both'
            return "EXISTENTE"

    merged["ESTADO_CUENTA"] = merged["_merge"].apply(get_estado)

    # PASO 4: Calcular Valores Financieros

    # SALDOFIN_2025: viene de SALDOFIN_CALC del año 1
    # Si no existe (cuenta NUEVA), será NaN
    merged["SALDOFIN_2025"] = merged.apply(
        lambda row: row.get("SALDOFIN_CALC_y1", np.nan)
        if pd.notna(row.get("SALDOFIN_CALC_y1"))
        else np.nan,
        axis=1,
    )

    # SALDO_INI_2026: viene de SALDO_INI del año 2
    # Si no existe (cuenta ELIMINADA), será NaN
    merged["SALDO_INI_2026"] = merged.apply(
        lambda row: row.get("SALDO_INI_y2", np.nan)
        if pd.notna(row.get("SALDO_INI_y2"))
        else np.nan,
        axis=1,
    )

    # DIFERENCIA: Siempre se calcula, incluso con NaN
    # Pandas maneja NaN - número = NaN automáticamente
    merged["DIFERENCIA"] = merged["SALDO_INI_2026"] - merged["SALDOFIN_2025"]

    # PASO 5: Rellenar Datos Base
    # Crear DataFrame resultado con las columnas finales
    result_data = {}

    # La clave primaria siempre existe
    result_data[pk_col] = merged[pk_col]

    # Para cada columna en la configuración
    for col in columns_csv:
        if col == pk_col:
            continue  # Ya la tenemos

        # Nombres de las columnas en el merge
        col_y1 = f"{col}_y1"
        col_y2 = f"{col}_y2"

        # Función para rellenar según estado
        def fill_column_value(row):
            estado = row["ESTADO_CUENTA"]

            # Para NUEVAS y EXISTENTES: priorizar year2
            if estado in ["NUEVA", "EXISTENTE"]:
                # Intentar obtener de year2
                if col_y2 in row and pd.notna(row[col_y2]):
                    return row[col_y2]
                # Si no existe, intentar de year1
                elif col_y1 in row and pd.notna(row[col_y1]):
                    return row[col_y1]
                else:
                    return np.nan

            # Para ELIMINADAS: usar year1
            else:  # ELIMINADA
                if col_y1 in row and pd.notna(row[col_y1]):
                    return row[col_y1]
                else:
                    return np.nan

        # Solo procesar si al menos una de las columnas existe
        if col_y1 in merged.columns or col_y2 in merged.columns:
            result_data[col] = merged.apply(fill_column_value, axis=1)
        else:
            # Si la columna no existe en ninguno, llenar con NaN
            result_data[col] = np.nan

    # Añadir las columnas calculadas
    result_data["SALDOFIN_2025"] = merged["SALDOFIN_2025"]
    result_data["SALDO_INI_2026"] = merged["SALDO_INI_2026"]
    result_data["DIFERENCIA"] = merged["DIFERENCIA"]
    result_data["ESTADO_CUENTA"] = merged["ESTADO_CUENTA"]

    # Crear DataFrame final
    result = pd.DataFrame(result_data)

    # PASO 6: Definir orden de columnas final
    final_columns = [
        pk_col,
        "COD_BANCO",
        "DESCRIP_BCO",
        "TIP_CTA",
        "DESCRIP_TIP_CTA",
        "MEDIO_PAGO",
        "DESCRIP_MEDIO_PGO",
        "NOM_CTA",
        "INGRESOS",
        "EGRESOS",
        "SALDO_INI",
        "CORRENT",
        "DESCRIP_ENTIDAD",
        "CLASE_CTA",
        "CUENTA_FONDO",
        "SECTOR",
        "DESCRIP_SECTOR",
        "COD_CTA_SAFYC",
        "SALDOFIN_2025",
        "SALDO_INI_2026",
        "DIFERENCIA",
        "ESTADO_CUENTA",
    ]

    # Seleccionar solo las columnas que existen
    existing_final_columns = [col for col in final_columns if col in result.columns]
    result = result[existing_final_columns]

    # PASO 7: Filtrar por diferencia != 0
    # Nota: En pandas, comparar con NaN siempre da False, pero queremos incluir NaN
    # Por lo tanto: incluir si DIFERENCIA != 0 OR DIFERENCIA es NaN
    has_difference = (result["DIFERENCIA"] != 0) | (result["DIFERENCIA"].isna())
    df_completa = result[has_difference].copy()

    print(f"Registros con diferencia (completa): {len(df_completa)}")
    print(f"  - NUEVAS: {len(df_completa[df_completa['ESTADO_CUENTA'] == 'NUEVA'])}")
    print(
        f"  - EXISTENTES: {len(df_completa[df_completa['ESTADO_CUENTA'] == 'EXISTENTE'])}"
    )
    print(
        f"  - ELIMINADAS: {len(df_completa[df_completa['ESTADO_CUENTA'] == 'ELIMINADA'])}"
    )

    # PASO 8: Generar DataFrame de solo existentes (sin ESTADO_CUENTA)
    df_existentes = df_completa[df_completa["ESTADO_CUENTA"] == "EXISTENTE"].copy()
    if "ESTADO_CUENTA" in df_existentes.columns:
        df_existentes = df_existentes.drop(columns=["ESTADO_CUENTA"])

    print(f"Registros con diferencia (solo existentes): {len(df_existentes)}")

    # PASO 9: Ordenar por COD_CTA_SAFYC (numérico)
    sort_col = "COD_CTA_SAFYC"
    if sort_col in df_completa.columns:
        df_completa = df_completa.sort_values(
            by=sort_col,
            key=lambda s: pd.to_numeric(s, errors="coerce"),
        ).reset_index(drop=True)
    else:
        df_completa = df_completa.sort_values(pk_col).reset_index(drop=True)

    if sort_col in df_existentes.columns:
        df_existentes = df_existentes.sort_values(
            by=sort_col,
            key=lambda s: pd.to_numeric(s, errors="coerce"),
        ).reset_index(drop=True)
    else:
        df_existentes = df_existentes.sort_values(pk_col).reset_index(drop=True)

    return df_completa, df_existentes


def get_comparison_summary(
    df_completa: pd.DataFrame, df_existentes: pd.DataFrame
) -> dict:
    """
    Genera un resumen estadístico de la comparación.

    Args:
        df_completa: DataFrame con todas las diferencias
        df_existentes: DataFrame con solo existentes

    Returns:
        dict: Resumen con estadísticas

    Example:
        >>> summary = get_comparison_summary(df_completa, df_existentes)
        >>> print(summary)
        {
            'total_diferencias': 33,
            'cuentas_nuevas': 16,
            'cuentas_existentes': 17,
            'cuentas_eliminadas': 0,
            ...
        }
    """
    summary = {
        "total_diferencias": len(df_completa),
        "cuentas_nuevas": len(df_completa[df_completa["ESTADO_CUENTA"] == "NUEVA"]),
        "cuentas_existentes": len(df_existentes),
        "cuentas_eliminadas": len(
            df_completa[df_completa["ESTADO_CUENTA"] == "ELIMINADA"]
        ),
    }

    # Estadísticas de diferencias en existentes (solo valores no-NaN)
    diferencias_existentes = df_existentes["DIFERENCIA"].dropna()

    if len(diferencias_existentes) > 0:
        summary.update(
            {
                "diferencia_promedio": float(diferencias_existentes.mean()),
                "diferencia_maxima": float(diferencias_existentes.max()),
                "diferencia_minima": float(diferencias_existentes.min()),
                "diferencia_total": float(diferencias_existentes.sum()),
            }
        )

    return summary
