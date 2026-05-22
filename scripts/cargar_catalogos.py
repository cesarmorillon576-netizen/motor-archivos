import os

import pandas as pd
from sqlmodel import Session

from data.db import engine, iniciar_bd
from data.constants import URLS_CATALOGOS
from helpers import (
    log,
    descargar_archivo,
    extraer_zip,
    escanear_directorio,
    obtener_modelo,
    procesar_archivo,
    normalizar_dataframe,
)
from helpers.sanitizer import transformar_para_modelo

# Catálogos que requieren descarga manual
_OMITIR_DESCARGA = {"loinc"}

# Orden de inserción para respetar las FK
_ORDEN_PRIORIDAD = [
    "entidad_federativa",
    "municipio",
    "localidad",
]

_BATCH_SIZE = 5_000


def descargar_catalogos(destino: str = "descargas") -> None:
    log.info("Iniciando descarga de catálogos oficiales...")

    for clave, url in URLS_CATALOGOS.items():
        if clave in _OMITIR_DESCARGA:
            log.info(f"Omitiendo '{clave}' (descarga manual requerida)")
            continue

        ext = os.path.splitext(url.split("?")[0])[1].lower() or ".xlsx"
        ruta = os.path.join(destino, f"{clave}_origen{ext}")

        exito = descargar_archivo(url, ruta)

        if exito and ext == ".zip":
            extraer_zip(ruta, os.path.join(destino, f"{clave}_extraido"))


def cargar_archivo(ruta: str, batch_size: int = _BATCH_SIZE) -> int:
    modelo = obtener_modelo(ruta)
    if not modelo:
        log.warning(f"Saltando '{os.path.basename(ruta)}': sin modelo mapeado")
        return 0

    df = procesar_archivo(ruta)
    if df is None or df.empty:
        log.warning(f"Saltando '{os.path.basename(ruta)}': DataFrame vacío o no legible")
        return 0

    df = normalizar_dataframe(df)
    df = transformar_para_modelo(df, modelo.__tablename__)
    df = df.where(pd.notna(df), None)

    if df.empty:
        log.warning(f"DataFrame vacío tras transformación para '{modelo.__tablename__}'")
        return 0

    total = len(df)
    log.info(f"Cargando {total} filas en tabla '{modelo.__tablename__}'...")

    with Session(engine, autoflush=False) as session:
        try:
            insertados = 0
            for i in range(0, total, batch_size):
                lote = df.iloc[i : i + batch_size]
                for _, fila in lote.iterrows():
                    datos = {k: v for k, v in fila.to_dict().items() if pd.notna(v)}
                    session.merge(modelo(**datos))
                    insertados += 1
                session.commit()
                log.info(f"  batch {i // batch_size + 1}: +{len(lote)} filas")

            log.info(f"✓ {insertados} filas sincronizadas en '{modelo.__tablename__}'")
            return insertados
        except Exception as e:
            session.rollback()
            log.error(f"Error al sincronizar '{modelo.__tablename__}': {e}")
            return 0


def orquestador(carpeta: str = "descargas") -> None:
    iniciar_bd()

    descargar_catalogos(carpeta)

    arbol = escanear_directorio(carpeta)
    archivos = arbol["excel"] + arbol["csv"]

    if not archivos:
        log.warning("No se encontraron archivos para procesar en disco.")
        return

    def prioridad(ruta: str) -> int:
        nombre = os.path.basename(ruta).lower()
        for i, clave in enumerate(_ORDEN_PRIORIDAD):
            if clave in nombre:
                return i
        return len(_ORDEN_PRIORIDAD)

    archivos.sort(key=prioridad)

    for archivo in archivos:
        log.info(f"Procesando: {os.path.basename(archivo)}")
        cargar_archivo(archivo)
        log.info("=" * 50)

    log.info("Catálogos actualizados.")


if __name__ == "__main__":
    orquestador()
