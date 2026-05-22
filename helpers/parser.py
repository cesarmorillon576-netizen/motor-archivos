import os
import re

import pandas as pd

import data
from .logger import log

# Lista ordenada de tuplas (regex, modelo).
# se usa el primer patrón que coincida.
MAPEO_MODELOS = [
    (r"diagnostico",              data.Diagnostico),
    (r"procedimiento",            data.Procedimiento),
    (r"loinc",                    data.Loinc),
    (r"lengua",                   data.LenguaIndigena),
    (r"religion",                 data.Religion),
    (r"formacion",                data.Formacion),
    (r"nacionalidad",             data.Nacionalidad),
    (r"entidad",                  data.EntidadFederativa),
    (r"municipio",                data.Municipio),
    (r"localidad",                data.Localidad),
    (r"codigo[_ ]?postal|^cp_",   data.CodigoPostal),
    (r"medicamento",              data.Medicamento),
    # TODO: CLUES y CIF pendientes de análisis
]


def obtener_modelo(ruta_archivo: str):
    nombre = os.path.basename(ruta_archivo).lower()
    for patron, modelo in MAPEO_MODELOS:
        if re.search(patron, nombre):
            log.info(f"Archivo '{nombre}' → tabla '{modelo.__tablename__}'")
            return modelo
    log.warning(f"Archivo '{nombre}' no corresponde a ningún modelo registrado")
    return None


def procesar_archivo(ruta_archivo: str) -> pd.DataFrame:
    if not os.path.exists(ruta_archivo):
        log.error(f"Archivo no encontrado: {ruta_archivo}")
        return pd.DataFrame()

    extension = os.path.splitext(ruta_archivo)[1].lower()
    log.info(f"Leyendo: {ruta_archivo}")

    try:
        read_opts = {"dtype": str, "keep_default_na": False}
        if extension in (".xlsx", ".xlsm"):
            df = pd.read_excel(ruta_archivo, engine="openpyxl", **read_opts)
        elif extension == ".xls":
            df = pd.read_excel(ruta_archivo, engine="xlrd", **read_opts)
        elif extension == ".csv":
            try:
                df = pd.read_csv(ruta_archivo, encoding="utf-8", **read_opts)
            except UnicodeDecodeError:
                log.warning(f"UTF-8 falló en {ruta_archivo}, reintentando con ISO-8859-1")
                df = pd.read_csv(ruta_archivo, encoding="ISO-8859-1", **read_opts)
        else:
            log.error(f"Extensión no soportada: {extension}")
            return pd.DataFrame()

        df.dropna(how="all", inplace=True)
        return df

    except Exception as e:
        log.error(f"Error al procesar {ruta_archivo}: {e}")
        return pd.DataFrame()
