"""
Script de ejemplo para probar la API en ejecución.

Primero inicia el servidor con: uvicorn main:app --reload
Luego ejecuta este script: python ejemplo_uso_api.py
"""

import requests
import os


def test_api_endpoint():
    """Prueba el endpoint de comparación de la API"""

    print("=" * 70)
    print("PRUEBA DE LA API - Endpoint /api/compare")
    print("=" * 70)

    # URL de la API (asegúrate de que el servidor esté corriendo)
    url = "http://localhost:8000/api/compare"

    # Verificar que los archivos existan
    csv1_path = "csv/2025.CSV"
    csv2_path = "csv/2026.CSV"

    if not os.path.exists(csv1_path):
        print(f"❌ Error: No se encontró {csv1_path}")
        return False

    if not os.path.exists(csv2_path):
        print(f"❌ Error: No se encontró {csv2_path}")
        return False

    print(f"\n✓ Archivos CSV encontrados")
    print(f"  - {csv1_path}")
    print(f"  - {csv2_path}")

    # Preparar archivos para el request
    print(f"\n📤 Enviando petición a {url}...")

    try:
        with open(csv1_path, "rb") as f1, open(csv2_path, "rb") as f2:
            files = {
                "file_year1": ("2025.CSV", f1, "text/csv"),
                "file_year2": ("2026.CSV", f2, "text/csv"),
            }

            # Hacer la petición
            response = requests.post(url, files=files, timeout=60)

        # Verificar respuesta
        if response.status_code == 200:
            print("✅ Petición exitosa!")

            # Guardar el ZIP
            output_filename = "comparacion_saldos_2025_2026.zip"
            with open(output_filename, "wb") as output:
                output.write(response.content)

            file_size = len(response.content)
            print(f"\n📦 Archivo ZIP generado: {output_filename}")
            print(f"   Tamaño: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

            # Verificar contenido del ZIP
            import zipfile

            with zipfile.ZipFile(output_filename, "r") as zip_ref:
                files_in_zip = zip_ref.namelist()
                print(f"\n📂 Contenido del ZIP:")
                for file in files_in_zip:
                    file_info = zip_ref.getinfo(file)
                    print(f"   - {file}: {file_info.file_size:,} bytes")

                # Extraer archivos
                extract_dir = "resultado_api"
                zip_ref.extractall(extract_dir)
                print(f"\n✓ Archivos extraídos en: {extract_dir}/")

            print("\n" + "=" * 70)
            print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
            print("=" * 70)

            return True

        else:
            print(f"❌ Error en la petición: Status {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
        return False

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_health_endpoint():
    """Prueba el endpoint de health check"""

    print("\n" + "=" * 70)
    print("PRUEBA DE LA API - Endpoint /health")
    print("=" * 70)

    url = "http://localhost:8000/health"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✅ Health check exitoso!")
            print(f"\n📊 Información del servicio:")
            for key, value in data.items():
                print(f"   - {key}: {value}")
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    import sys

    print("\n🚀 Iniciando pruebas de la API...")
    print("   (Asegúrate de que el servidor esté corriendo en http://localhost:8000)")
    print()

    # Probar health endpoint
    health_ok = test_health_endpoint()

    if not health_ok:
        print("\n❌ El servidor no está disponible. Inicíalo con:")
        print("   uvicorn main:app --reload")
        sys.exit(1)

    # Probar endpoint principal
    api_ok = test_api_endpoint()

    sys.exit(0 if api_ok else 1)
