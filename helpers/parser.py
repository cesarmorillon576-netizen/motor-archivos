import io
import os
import re
import zipfile

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
    (r"clues",                    data.CLUES),
    # TODO: CIF pendiente de análisis
]


def _parchear_xlsx(ruta_archivo: str) -> io.BytesIO:
    """
    Crea una copia en memoria del xlsx corrigiendo valores de font family > 14
    que openpyxl rechaza aunque Excel los acepta sin problema.
    """
    buf_out = io.BytesIO()
    _ARCHIVOS_CON_FAMILY = {"xl/sharedStrings.xml", "xl/styles.xml"}

    def _clamp_family(text: str) -> str:
        return re.sub(
            r'(<family\b[^>]*\bval=")(\d+)(")',
            lambda m: m.group(1) + str(min(int(m.group(2)), 14)) + m.group(3),
            text,
        )

    with zipfile.ZipFile(ruta_archivo, "r") as zin, \
         zipfile.ZipFile(buf_out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in _ARCHIVOS_CON_FAMILY:
                data = _clamp_family(data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)
    buf_out.seek(0)
    return buf_out


def obtener_modelo(ruta_archivo: str, log_match: bool = True):
    nombre = os.path.basename(ruta_archivo).lower()
    for patron, modelo in MAPEO_MODELOS:
        if re.search(patron, nombre):
            if log_match:
                log.info(f"Archivo '{nombre}' → tabla '{modelo.__tablename__}'")
            return modelo
    if log_match:
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
            try:
                df = pd.read_excel(ruta_archivo, engine="openpyxl", **read_opts)
            except Exception as openpyxl_err:
                log.warning(f"openpyxl falló, parcheando font family inválido: {openpyxl_err}")
                try:
                    df = pd.read_excel(_parchear_xlsx(ruta_archivo), engine="openpyxl", **read_opts)
                except Exception as e2:
                    log.error(f"Error al procesar {ruta_archivo}: {e2}")
                    return pd.DataFrame()
        elif extension == ".xls":
            all_sheets = pd.read_excel(ruta_archivo, engine="xlrd", sheet_name=None, **read_opts)
            from collections import Counter
            col_tuples = [tuple(s.columns) for s in all_sheets.values() if not s.empty]
            if col_tuples:
                cols_comunes = Counter(col_tuples).most_common(1)[0][0]
                hojas_validas = [s for s in all_sheets.values() if tuple(s.columns) == cols_comunes and not s.empty]
                df = pd.concat(hojas_validas, ignore_index=True)
            else:
                df = pd.DataFrame()
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
