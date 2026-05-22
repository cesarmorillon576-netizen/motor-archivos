import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db import iniciar_bd
from helpers.logger import log
from scripts.sincronizador import sincronizar_en_disco
from scripts.pipeline import insertar_bd

# Orden de inserción para respetar las FK
_ORDEN_PRIORIDAD = [
    "entidad_federativa",
    "municipio",
    "localidad",
]

def orquestador(carpeta: str = "descargas") -> None:
    log.info("=== Iniciando sistema de actualizacion de catálogos ===")
    iniciar_bd()

    archivos_modificados = sincronizar_en_disco(carpeta)

    if not archivos_modificados:
        log.info("Todos los catálogos están al día. Nada que procesar")
        return
    def prioridad(ruta: str) -> int:
        nombre = os.path.basename(ruta).lower()
        for i, clave in enumerate(_ORDEN_PRIORIDAD):
            if clave in nombre:
                return i
        return len(_ORDEN_PRIORIDAD)

    archivos_modificados.sort(key=prioridad)

    for archivo in archivos_modificados:
        log.info(f"Procesando: {os.path.basename(archivo)}")
        insertar_bd(archivo)
        log.info("=" * 50)

    log.info("=== Sistema de actualizacion de catálogos finalizado ===")


if __name__ == "__main__":
    orquestador()
