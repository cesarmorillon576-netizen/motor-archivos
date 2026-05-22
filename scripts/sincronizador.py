import os
from data.constants import URLS_CATALOGOS
from helpers.logger import log
from helpers.extractor import descargar_archivo, extraer_zip
from helpers.hasher import comparar_bytes

_OMITIR_DESCARGA = {"loinc"}

def sincronizar_en_disco(directorio_base: str) -> list[str]:
    """
    Descarga los catálogos temporalmente para comprar hashes y actualizar registros
    """

    carpeta_temporal = os.path.join(directorio_base, "temporales")
    catalogos_modificados = []

    for clave, url in URLS_CATALOGOS.items():
        if clave in _OMITIR_DESCARGA:
            log.info(f"Omitiendo descarga de {clave}")
            continue

        ext = os.path.splitext(url.split("?")[0])[1].lower() or ".xlsx"
        ruta_tmp = os.path.join(carpeta_temporal, f"{clave}_origen{ext}")
        ruta_final = os.path.join(directorio_base, f"{clave}_origen{ext}")

        if not descargar_archivo(url, ruta_tmp):
            log.error(f"Sincronizacion fallida para: {clave}")
            continue

        if comparar_bytes(ruta_tmp, ruta_final):
            log.info(f"Cambio detectado en catálogo: '{clave}'")

            if os.path.exists(ruta_final):
                os.remove(ruta_final)
            os.rename(ruta_tmp, ruta_final)

            if ext == ".zip":
                ruta_extraccion = os.path.join(directorio_base, f"{clave}_extraido")
                extraer_zip(ruta_final, ruta_extraccion)
                for nombre_archivo in os.listdir(ruta_extraccion):
                    ruta_archivo = os.path.join(ruta_extraccion, nombre_archivo)
                    if os.path.isfile(ruta_archivo):
                        catalogos_modificados.append(ruta_archivo)
            else:
                catalogos_modificados.append(ruta_final)
        else:
            log.info(f"Catálogo '{clave}' sin cambios...")
            if os.path.exists(ruta_tmp):
                os.remove(ruta_tmp)
    return catalogos_modificados
