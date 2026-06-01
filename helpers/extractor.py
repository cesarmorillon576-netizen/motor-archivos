import os
import zipfile
from urllib.parse import urlparse

import requests
import urllib3

from .logger import log

# Dominios con SSL invalido (gracias gobierno de mechico)
_DOMINIOS_SSL_RELAJADO = {
    "csg.gob.mx",  
}


def descargar_archivo(
    url: str, destino: str, auth: tuple[str, str] | None = None
) -> bool:
    try:
        log.info(f"Descargando archivo desde {url}")

        host = urlparse(url).hostname or ""
        verify_ssl = host not in _DOMINIOS_SSL_RELAJADO

        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            log.warning(f"SSL relajado para {host} (dominio en whitelist)")

        response = requests.get(
            url, timeout=30, stream=True, verify=verify_ssl, auth=auth
        )
        response.raise_for_status()

        os.makedirs(os.path.dirname(destino), exist_ok=True)

        with open(destino, "wb") as f:
            for bloque in response.iter_content(chunk_size=8192):
                f.write(bloque)

        log.info(f"Archivo guardado en {destino}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"Error de red al descargar desde {url}: {e}")
        return False
    except Exception as e:
        log.error(f"Error al guardar {destino}: {e}")
        return False


def resolver_descarga_loinc(url: str, auth: tuple[str, str] | None = None) -> str | None:
    """
    El endpoint de LOINC no devuelve el ZIP, sino una metadata JSON cuyo campo
    'downloadUrl' apunta al ZIP real. Devuelve esa URL (o None si falla).
    """
    try:
        log.info(f"Resolviendo URL de descarga de LOINC desde {url}")
        response = requests.get(url, timeout=30, auth=auth)
        response.raise_for_status()
        return response.json()["downloadUrl"]
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        log.error(f"No se pudo resolver la URL de descarga de LOINC: {e}")
        return None


def extraer_archivo_de_zip(ruta_zip: str, nombre_interno: str, destino: str) -> str | None:
    """
    Extrae un único miembro del ZIP (por su ruta interna) en lugar de todo el árbol.
    Útil cuando el ZIP trae muchos archivos y solo interesa uno (ej. LOINC).
    Devuelve la ruta del archivo extraído o None si falla.
    """
    try:
        if not os.path.exists(ruta_zip):
            log.error(f"El archivo ZIP {ruta_zip} no existe")
            return None

        log.info(f"Extrayendo '{nombre_interno}' desde {ruta_zip}")
        os.makedirs(destino, exist_ok=True)

        with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
            ruta_extraida = zip_ref.extract(nombre_interno, destino)

        log.info(f"Archivo extraído en {ruta_extraida}")
        return ruta_extraida
    except KeyError:
        log.error(f"'{nombre_interno}' no existe dentro de {ruta_zip}")
        return None
    except zipfile.BadZipFile as e:
        log.error(f"{ruta_zip} no es un ZIP válido: {e}")
        return None
    except Exception as e:
        log.error(f"Error al extraer '{nombre_interno}' de {ruta_zip}: {e}")
        return None


def extraer_zip(ruta_zip: str, destino: str) -> bool:
    try:
        if not os.path.exists(ruta_zip):
            log.error(f"El archivo ZIP {ruta_zip} no existe")
            return False

        log.info(f"Extrayendo ZIP desde {ruta_zip}")
        os.makedirs(destino, exist_ok=True)

        with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
            zip_ref.extractall(destino)

        log.info(f"ZIP extraído en {destino}")
        return True
    except zipfile.BadZipFile as e:
        log.error(f"{ruta_zip} no es un ZIP válido: {e}")
        return False
    except Exception as e:
        log.error(f"Error al extraer {ruta_zip}: {e}")
        return False
