import hashlib
import os

def calcular_sha256(ruta_archivo: str) -> str:
    """
    Calcula el hash SHA256 de un archivo.
    """

    sha256_hash = hashlib.sha256()
    try:
        with open(ruta_archivo, "rb") as f:
            for bloque in iter(lambda: f.read(4096), b""):
                sha256_hash.update(bloque)
        return sha256_hash.hexdigest()    
    except FileNotFoundError:
        return "" 

def comparar_bytes(ruta_temporal: str, ruta_final: str) -> bool:
    """
    compara el hash del archivo con el archivo con ultima eejecucion exitosa
    """

    if not os.path.exists(ruta_final):
        return True

    hash_temporal = calcular_sha256(ruta_temporal)
    hash_final = calcular_sha256(ruta_final)

    return hash_temporal != hash_final