import os
import zipfile
from urllib.parse import urlparse

import requests
import urllib3

from .logger import log

# Dominios con certificado SSL inválido pero fuente oficial y pública.
# Expandir solo con justificación documentada; retirar cuando el cert sea corregido.
_DOMINIOS_SSL_RELAJADO = {
    "csg.gob.mx",  # Compendio Nacional de Insumos para la Salud (hostname mismatch)
}


def descargar_archivo(url: str, destino: str) -> bool:
    try:
        log.info(f"Descargando archivo desde {url}")

        host = urlparse(url).hostname or ""
        verify_ssl = host not in _DOMINIOS_SSL_RELAJADO

        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            log.warning(f"SSL relajado para {host} (dominio en whitelist)")

        response = requests.get(url, timeout=30, stream=True, verify=verify_ssl)
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
