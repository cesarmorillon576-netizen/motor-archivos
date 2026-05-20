import os
from data import engine, Session, URLS_CATALOGOS
from helpers import (
    log, descargar_archivo, extraer_zip, escanear_directorio,
    obtener_modelo, procesar_archivo, normalizar_dataframe
)

def descargar_catalogos():
    log.info(f"Iniciando descarga dde catálogos oficiales...")

    for clave, url in URLS_CATALOGOS.items:
        if "loinc" in clave:
            log.info("Saltando descarga automática de LOINC")
            continue

        extension = ".zip" if ".zip" in url.lower() else ".xlsx"
        ruta_descarga = f"descargas/{clave}_origen{extension}"       

        exito = descargar_archivo(url, ruta_descarga )

        if exito and extension == ".zip":
            carpeta_destino = f"descargas/{clave}_extraido"
            extraer_zip(ruta_descarga, carpeta_destino)    