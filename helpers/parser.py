import os
import pandas as pd
import data
from .logger import log

# Diccionario para clases con sus modelos
MAPEO_MODELOS = {
    "diagnostico": data.Diagnostico,
    "procedimiento": data.Procedimiento,
    "loinc": data.LOINC,
    "lengua": data.LenguaIndigena,
    "religion": data.Religion,
    "formacion": data.Formacion,
    "nacionalidad": data.Nacionalidad,
    "entidad": data.EntidadFederativa,
    "municipio": data.Municipio,
    "localidad": data.Localidad,
    "cp": data.CodigoPostal,
    "medicamento": data.Medicamento
}

def obtener_modelo(ruta_archivo: str):
    nombre_base = os.path.basename(ruta_archivo).lower()

    for clave, modelo in MAPEO_MODELOS.items():
        if clave in nombre_base:
            log.info(f"Archivo {ruta_archivo} corresponde a {clave}")
            return modelo
    
    log.warning(f"Archivo {ruta_archivo} no corresponde a ningún modelo")
    return None

def procesar_archivo(ruta_archivo: str) -> pd.DataFrame:
    if not os.path.exists(ruta_archivo):
        log.error(f"Archivo {ruta_archivo} no existe")
        return None
    
    extension = os.path.splitext(ruta_archivo)[1].lower()
    log.info(f"Leyendo datos de archivo fisico: {ruta_archivo}")
    
    try:
        if extension in ['.xlsx', '.xlsm']:
            df = pd.read_excel(ruta_archivo, engine='openpyxl')
        elif extension == '.xls':
            df = pd.read_excel(ruta_archivo, engine='xlrd')
        elif extension == '.csv':
            df = pd.read_csv(ruta_archivo, encoding='utf-8')
        else:
            raise ValueError(f"Extension de archivo '{extension}' no soportado")
            
        df.dropna(how='all', inplace=True)
        return df
    except UnicodeDecodeError:
        log.warning("Error de encoding UTF-8 detectado.")
        return pd.read_csv(ruta_archivo, encoding='ISO-8859-1')
    except Exception as e:
        log.error(f"Error al procesar archivo {ruta_archivo}: {str(e)}")
        return pd.DataFrame()