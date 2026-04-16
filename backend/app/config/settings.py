"""
Configuración de la aplicación.
Carga y gestiona la configuración desde data.json.
"""

import json
from pathlib import Path
from typing import Dict, List


class Settings:
    """
    Clase para gestionar la configuración de la aplicación.
    Carga los parámetros desde data.json.
    """

    def __init__(self):
        # Ruta al archivo data.json en la raíz del proyecto
        self.project_root = Path(__file__).parent.parent.parent
        self.data_json_path = self.project_root / "data.json"
        self._config = None

    def load_config(self) -> Dict:
        """
        Carga configuración desde data.json.
        Utiliza caché para evitar lecturas repetidas.

        Returns:
            dict: Configuración completa del archivo JSON

        Raises:
            FileNotFoundError: Si data.json no existe
            json.JSONDecodeError: Si el JSON está mal formado
        """
        if self._config is None:
            if not self.data_json_path.exists():
                raise FileNotFoundError(
                    f"No se encontró el archivo de configuración: {self.data_json_path}"
                )

            with open(self.data_json_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)

        return self._config

    @property
    def columns_csv(self) -> List[str]:
        """
        Retorna lista de columnas relevantes definidas en data.json.

        Returns:
            list: Lista de nombres de columnas

        Example:
            >>> settings = Settings()
            >>> columns = settings.columns_csv
            >>> print(columns)
            ['COD_BANCO', 'DESCRIP_BCO', 'TIP_CTA', ...]
        """
        config = self.load_config()
        return config.get("COLUMNS_CSV", [])

    @property
    def pk_column(self) -> str:
        """
        Retorna nombre de la columna clave primaria.

        Returns:
            str: Nombre de la columna PK (normalmente 'COD_CTA_FMT')

        Example:
            >>> settings = Settings()
            >>> pk = settings.pk_column
            >>> print(pk)
            'COD_CTA_FMT'
        """
        config = self.load_config()
        return config.get("PK_COL", "COD_CTA_FMT")

    @property
    def numeric_columns(self) -> List[str]:
        """
        Retorna lista de columnas que deben ser tratadas como numéricas.

        Returns:
            list: Lista de nombres de columnas numéricas
        """
        return ["SALDO_INI", "SALDOFIN_CALC", "INGRESOS", "EGRESOS"]


# Instancia global de configuración
settings = Settings()
