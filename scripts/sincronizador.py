import os
from data.constants import URLS_CATALOGOS
from data.config import settings
from helpers.logger import log
from helpers.extractor import (
    descargar_archivo,
    extraer_zip,
    extraer_archivo_de_zip,
    resolver_descarga_loinc,
)
from helpers.hasher import comparar_bytes

_OMITIR_DESCARGA = set()

# Catálogos que requieren autenticación (Basic Auth por GET)
_CATALOGOS_CON_AUTH = {
    "loinc": (settings.LOINC_USER, settings.LOINC_PASSWORD),
}

# Extensión forzada para catálogos cuya URL no la revela (ej. endpoints /api/)
_EXTENSION_FORZADA = {
    "loinc": ".zip",
}

# Catálogos cuya URL apunta a metadata; hay que resolver la URL real del archivo
_RESOLVEDORES_URL = {
    "loinc": resolver_descarga_loinc,
}

# ZIPs con muchos archivos donde solo interesa una ruta interna concreta
_ARCHIVO_EN_ZIP = {
    "loinc": "LoincTable/Loinc.csv",
}

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

        ext = _EXTENSION_FORZADA.get(clave) or os.path.splitext(url.split("?")[0])[1].lower() or ".xlsx"
        ruta_tmp = os.path.join(carpeta_temporal, f"{clave}_origen{ext}")
        ruta_final = os.path.join(directorio_base, f"{clave}_origen{ext}")

        auth = _CATALOGOS_CON_AUTH.get(clave)

        resolver = _RESOLVEDORES_URL.get(clave)
        if resolver:
            url = resolver(url, auth)
            if not url:
                log.error(f"Sincronizacion fallida para: {clave}")
                continue

        if not descargar_archivo(url, ruta_tmp, auth=auth):
            log.error(f"Sincronizacion fallida para: {clave}")
            continue

        if comparar_bytes(ruta_tmp, ruta_final):
            log.info(f"Cambio detectado en catálogo: '{clave}'")

            if os.path.exists(ruta_final):
                os.remove(ruta_final)
            os.rename(ruta_tmp, ruta_final)

            if ext == ".zip":
                ruta_extraccion = os.path.join(directorio_base, f"{clave}_extraido")
                interno = _ARCHIVO_EN_ZIP.get(clave)
                if interno:
                    ruta_archivo = extraer_archivo_de_zip(ruta_final, interno, ruta_extraccion)
                    if ruta_archivo:
                        catalogos_modificados.append(ruta_archivo)
                else:
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
