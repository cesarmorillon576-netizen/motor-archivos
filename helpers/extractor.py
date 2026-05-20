import os
import zipfile
import requests
from .logger import log

def descargar_archivo(url: str, destino: str) -> bool:
    try:
        log.info(f"Descargando archivo desde {url}")

        response = requests.get(url, timeout = 30, stream = True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        with open(destino, 'wb') as f:
            for bloque in response.iter_content(chunk_size=8192):
                f.write(bloque)
        
        log.info(f"Archivo descargado correctamente y guardado en {destino}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"Error de red al intentar descargar desde {url}: {str(e)}")
        return False
    except Exception as e:
        log.error(f"Error inesperado al guardar el archivo {destino}: {str(e)}")
        return False

def extraer_zip(ruta_zip: str, destino: str) -> bool:
    try:
        if not os.path.exists(ruta_zip):
            log.error(f"El archivo ZIP {ruta_zip} no existe")
            return False
        
        log.info(f"Extrayendo archivo ZIP desde {ruta_zip}")
        
        os.makedirs(destino, exist_ok=True)

        with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
            zip_ref.extractall(destino)
        
        log.info(f"Archivo ZIP extraído correctamente en {destino}")
        return True
    except zipfile.BadZipFile as e:
        log.error(f"Error: El archivo {ruta_zip} no es un archivo ZIP válido: {str(e)}")
        return False
    except Exception as e:
        log.error(f"Error inesperado al extraer el archivo ZIP {ruta_zip}: {str(e)}")
        return False