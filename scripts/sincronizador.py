import os
from sqlalchemy import text
from data.constants import URLS_CATALOGOS
from data.config import settings
from data.db import engine
from helpers.logger import log
from helpers.parser import obtener_modelo
from helpers.extractor import (
    descargar_archivo,
    extraer_zip,
    extraer_archivo_de_zip,
    resolver_descarga_loinc,
)
from helpers.hasher import comparar_bytes

_OMITIR_DESCARGA = set()

# Catálogos que requieren autenticación (Basic Auth por GET)
_CATALOGOS_CON_AUTH: dict[str, tuple[str, str]] = {}
if settings.LOINC_USER and settings.LOINC_PASSWORD:
    _CATALOGOS_CON_AUTH["loinc"] = (settings.LOINC_USER, settings.LOINC_PASSWORD)

_EXTENSION_FORZADA = {
    "loinc": ".zip",
}

_RESOLVEDORES_URL = {
    "loinc": resolver_descarga_loinc,
}

_ARCHIVO_EN_ZIP = {
    "loinc": "LoincTable/Loinc.csv",
}

def _materializar_datos(
    clave: str, ruta_final: str, ext: str, directorio_base: str, forzar: bool = False
) -> list[str]:
    """Devuelve las rutas de los archivos de datos listos para insertar.
    Para catálogos planos es el propio archivo. Para ZIPs extrae el contenido
    (o reutiliza la extracción previa, salvo `forzar=True` tras un cambio real)."""
    if ext != ".zip":
        return [ruta_final]

    ruta_extraccion = os.path.join(directorio_base, f"{clave}_extraido")
    interno = _ARCHIVO_EN_ZIP.get(clave)

    if interno:
        destino = os.path.join(ruta_extraccion, interno)
        if forzar or not os.path.exists(destino):
            ruta = extraer_archivo_de_zip(ruta_final, interno, ruta_extraccion)
            return [ruta] if ruta else []
        return [destino]

    if forzar or not os.path.isdir(ruta_extraccion):
        extraer_zip(ruta_final, ruta_extraccion)
    if not os.path.isdir(ruta_extraccion):
        return []
    return [
        os.path.join(ruta_extraccion, n)
        for n in os.listdir(ruta_extraccion)
        if os.path.isfile(os.path.join(ruta_extraccion, n))
    ]


def _tabla_pendiente(ruta_datos: str) -> bool:
    """True si el archivo mapea a un modelo cuya tabla no existe o está vacía en la BD.

    Permite que un catálogo sin cambios en disco se recargue cuando su tabla
    aún no tiene datos (modelo nuevo, o tabla borrada/truncada manualmente)."""
    modelo = obtener_modelo(ruta_datos, log_match=False)
    if not modelo:
        return False
    tabla = modelo.__tablename__
    try:
        with engine.connect() as conn:
            if conn.execute(text("SELECT to_regclass(:t)"), {"t": tabla}).scalar() is None:
                return True
            return conn.execute(text(f'SELECT count(*) FROM "{tabla}"')).scalar() == 0
    except Exception as e:
        log.warning(f"No se pudo verificar la tabla '{tabla}' en la BD: {e}")
        return False


def sincronizar_en_disco(directorio_base: str) -> list[str]:
    """
    Descarga los catálogos temporalmente para comparar hashes y actualizar registros.

    Un catálogo se procesa si (a) cambió respecto a la copia en disco, o
    (b) no cambió pero su tabla en la BD está vacía o no existe.
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

            catalogos_modificados.extend(
                _materializar_datos(clave, ruta_final, ext, directorio_base, forzar=True)
            )
        else:
            if os.path.exists(ruta_tmp):
                os.remove(ruta_tmp)

            # Sin cambios en disco, pero la BD podría estar vacía (modelo nuevo o
            # tabla borrada). Se verifica contra la BD antes de descartar el catálogo.
            rutas_datos = _materializar_datos(clave, ruta_final, ext, directorio_base)
            pendientes = [r for r in rutas_datos if r and _tabla_pendiente(r)]
            if pendientes:
                log.info(f"Catálogo '{clave}' sin cambios en disco, pero su tabla está vacía → recargando")
                catalogos_modificados.extend(pendientes)
            else:
                log.info(f"Catálogo '{clave}' sin cambios...")
    return catalogos_modificados
