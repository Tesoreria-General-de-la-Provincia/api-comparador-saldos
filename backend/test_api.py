"""
Script de prueba para verificar que la API funciona correctamente.
"""

import sys
import os

# Configurar encoding para Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.csv_reader import read_csv_file
from app.services.comparison_service import compare_dataframes, get_comparison_summary
from app.utils.excel_writer import create_comparison_excels
from fastapi import UploadFile
import asyncio


class MockUploadFile:
    """Mock de UploadFile para testing"""

    def __init__(self, filename, filepath):
        self.filename = filename
        self.filepath = filepath

    async def read(self):
        with open(self.filepath, "rb") as f:
            return f.read()


async def test_comparison():
    """Prueba la comparación con los archivos CSV de ejemplo"""
    print("=" * 70)
    print("PRUEBA DE COMPARACIÓN DE SALDOS")
    print("=" * 70)

    # Rutas a los archivos CSV de ejemplo
    csv1_path = "csv/2025.CSV"
    csv2_path = "csv/2026.CSV"

    # Verificar que existan
    if not os.path.exists(csv1_path):
        print(f"❌ Error: No se encontró {csv1_path}")
        return False

    if not os.path.exists(csv2_path):
        print(f"❌ Error: No se encontró {csv2_path}")
        return False

    print(f"\n✓ Archivos encontrados:")
    print(f"  - {csv1_path}")
    print(f"  - {csv2_path}")

    # Crear mocks de UploadFile
    print("\n" + "─" * 70)
    print("PASO 1: Lectura de archivos CSV")
    print("─" * 70)

    file1 = MockUploadFile("2025.CSV", csv1_path)
    file2 = MockUploadFile("2026.CSV", csv2_path)

    try:
        df1, year1 = await read_csv_file(file1)
        print(f"✓ Archivo 1 leído: año {year1}, {len(df1)} registros")

        df2, year2 = await read_csv_file(file2)
        print(f"✓ Archivo 2 leído: año {year2}, {len(df2)} registros")

    except Exception as e:
        print(f"❌ Error al leer archivos: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Comparar
    print("\n" + "─" * 70)
    print("PASO 2: Comparación de datos")
    print("─" * 70)

    try:
        df_completa, df_existentes = compare_dataframes(df1, df2, year1, year2)
        print(f"\n✓ Comparación completada")
        print(f"  - Registros en comparacion_completa: {len(df_completa)}")
        print(f"  - Registros en comparacion_existentes: {len(df_existentes)}")

        # Mostrar distribución por estado
        if "ESTADO_CUENTA" in df_completa.columns:
            print("\n  Distribución por estado:")
            for estado, count in df_completa["ESTADO_CUENTA"].value_counts().items():
                print(f"    - {estado}: {count}")

    except Exception as e:
        print(f"❌ Error en comparación: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Generar resumen
    print("\n" + "─" * 70)
    print("PASO 3: Resumen estadístico")
    print("─" * 70)

    try:
        summary = get_comparison_summary(df_completa, df_existentes)
        print("\n✓ Resumen generado:")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"  - {key}: {value:,.2f}")
            else:
                print(f"  - {key}: {value}")
    except Exception as e:
        print(f"⚠ Advertencia al generar resumen: {e}")

    # Generar Excel
    print("\n" + "─" * 70)
    print("PASO 4: Generación de archivos Excel")
    print("─" * 70)

    try:
        excel1, excel2 = create_comparison_excels(df_completa, df_existentes)
        print(f"\n✓ Archivos Excel generados:")
        print(f"  - comparacion_completa.xlsx: {len(excel1):,} bytes")
        print(f"  - comparacion_existentes.xlsx: {len(excel2):,} bytes")

        # Guardar archivos de prueba
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)

        with open(f"{output_dir}/comparacion_completa.xlsx", "wb") as f:
            f.write(excel1)

        with open(f"{output_dir}/comparacion_existentes.xlsx", "wb") as f:
            f.write(excel2)

        print(f"\n✓ Archivos guardados en {output_dir}/")

    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Validación de columnas
    print("\n" + "─" * 70)
    print("PASO 5: Validación de estructura")
    print("─" * 70)

    expected_columns = [
        "COD_CTA_FMT",
        "SALDOFIN_2025",
        "SALDO_INI_2026",
        "DIFERENCIA",
        "ESTADO_CUENTA",
    ]

    all_present = all(col in df_completa.columns for col in expected_columns)

    if all_present:
        print("✓ Todas las columnas esperadas están presentes")
    else:
        missing = [col for col in expected_columns if col not in df_completa.columns]
        print(f"⚠ Columnas faltantes: {missing}")

    # Verificar valores
    print("\n  Verificación de valores:")

    # Verificar que haya registros NUEVOS, EXISTENTES
    estados = df_completa["ESTADO_CUENTA"].unique()
    print(f"  - Estados encontrados: {', '.join(estados)}")

    # Verificar que las diferencias se calculen
    diferencias_no_nulas = df_completa["DIFERENCIA"].notna().sum()
    diferencias_nulas = df_completa["DIFERENCIA"].isna().sum()
    print(f"  - Diferencias calculadas: {diferencias_no_nulas}")
    print(f"  - Diferencias NaN: {diferencias_nulas}")

    # Mostrar algunas filas de ejemplo
    print("\n" + "─" * 70)
    print("PASO 6: Ejemplos de registros")
    print("─" * 70)

    print("\nEjemplo de cuenta EXISTENTE:")
    existentes = df_completa[df_completa["ESTADO_CUENTA"] == "EXISTENTE"].head(1)
    if not existentes.empty:
        row = existentes.iloc[0]
        print(f"  COD_CTA_FMT: {row['COD_CTA_FMT']}")
        print(f"  SALDOFIN_2025: {row['SALDOFIN_2025']}")
        print(f"  SALDO_INI_2026: {row['SALDO_INI_2026']}")
        print(f"  DIFERENCIA: {row['DIFERENCIA']}")

    if "NUEVA" in estados:
        print("\nEjemplo de cuenta NUEVA:")
        nuevas = df_completa[df_completa["ESTADO_CUENTA"] == "NUEVA"].head(1)
        if not nuevas.empty:
            row = nuevas.iloc[0]
            print(f"  COD_CTA_FMT: {row['COD_CTA_FMT']}")
            print(f"  SALDOFIN_2025: {row['SALDOFIN_2025']}")
            print(f"  SALDO_INI_2026: {row['SALDO_INI_2026']}")
            print(f"  DIFERENCIA: {row['DIFERENCIA']}")

    if "ELIMINADA" in estados:
        print("\nEjemplo de cuenta ELIMINADA:")
        eliminadas = df_completa[df_completa["ESTADO_CUENTA"] == "ELIMINADA"].head(1)
        if not eliminadas.empty:
            row = eliminadas.iloc[0]
            print(f"  COD_CTA_FMT: {row['COD_CTA_FMT']}")
            print(f"  SALDOFIN_2025: {row['SALDOFIN_2025']}")
            print(f"  SALDO_INI_2026: {row['SALDO_INI_2026']}")
            print(f"  DIFERENCIA: {row['DIFERENCIA']}")

    print("\n" + "=" * 70)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print(f"\nArchivos generados en: {os.path.abspath(output_dir)}/")

    return True


if __name__ == "__main__":
    result = asyncio.run(test_comparison())
    sys.exit(0 if result else 1)
