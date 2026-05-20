import os
from .logger import log

def escanear_directorio(ruta_raiz: str) -> dict:
    if not os.path.exists(ruta_raiz):
        log.error(f"La ruta {ruta_raiz} no existe")
        raise FileNotFoundError(f"La ruta {ruta_raiz} no existe")
    
    archivo_arbol = {
        "excel": [],
        "csv": [],
        "zip": [],
        "desconocido": []
    }
    
    for raiz, _, archivos in os.walk(ruta_raiz):
        for archivo in archivos:
            ruta_completa = os.path.join(raiz, archivo)
            extension = os.path.splitext(archivo)[1].lower()
            
            if extension in ['.xlsx', '.xlsm', '.xls']:
                archivo_arbol["excel"].append(ruta_completa)
            elif extension == '.csv':
                archivo_arbol["csv"].append(ruta_completa)
            elif extension in ['.zip', '.rar']:
                archivo_arbol["zip"].append(ruta_completa)
            else:
                archivo_arbol["desconocido"].append(ruta_completa)
    
    return archivo_arbol

def buscar_archivo_arbol(ruta_raiz: str, palabra_clave: str) -> str | None:
    if not os.path.exists(ruta_raiz):
        log.error(f"La ruta {ruta_raiz} no existe")
        return None
    
    log.info(f"Buscando el catalogo {palabra_clave} en {ruta_raiz}")
    palabra_clave = palabra_clave.lower()

    for raiz, _, archivos in os.walk(ruta_raiz):
        for archivo in archivos:
            if palabra_clave in archivo.lower():
                ruta_final = os.path.join(raiz, archivo)
                log.info(f"Catalogo encontrado en_ {ruta_final}")
                return ruta_final
    
    log.warning(f"No se encontró ningún archivo que coincida con {palabra_clave} en {ruta_raiz}")
    return None
    
    