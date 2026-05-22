import os
import pandas as pd
from sqlmodel import Session
from data.db import engine
from helpers.logger import log
from helpers.parser import obtener_modelo, procesar_archivo
from helpers.sanitizer import normalizar_dataframe, transformar_para_modelo

_BATCH_SIZE = 5_000

def insertar_bd(ruta: str, batch_size: int = _BATCH_SIZE) -> int:
    """" 
    Ciclo ETL para un archivo
    """
    modelo = obtener_modelo(ruta)
    if not modelo:
        log.warning(f"Saltando '{os.path.basename(ruta)}': sin modelo mapeado")
        return 0
    
    df = procesar_archivo(ruta)
    if df is None or df.empty:
        log.warning(f"Saltando '{os.path.basename(ruta)}': DataFrame vacio o no legible")
        return 0

    df = normalizar_dataframe(df)
    df = transformar_para_modelo(df, modelo.__tablename__)
    df = df.where(pd.notna(df), None)

    if df.empty:
        log.warning(f"DataFrame vacio tras transformacion para '{modelo.__tablename__}'")
        return 0

    total = len(df)
    log.info(f"Cargando {total} filas en tabla '{modelo.__tablename__}'...")

    with Session(engine, autoflush=False) as session:
        try:
            insertados = 0
            for i in range(0, total, batch_size):
                lote = df.iloc[i : i + batch_size]
                for _, fila in lote.iterrows():
                    datos = {
                        k: v for k, v in fila.to_dict().items() if pd.notna(v)
                    }
                    session.merge(modelo(**datos))
                    insertados += 1
                session.commit()
                log.info(f"lote {i//batch_size + 1} +  {len(lote)} filas")

            log.info(f" {insertados} filas sincronizadas en '{modelo.__tablename__}'")
            return insertados
        except Exception as e:
            session.rollback()
            log.error(f"Error al sincronizar '{modelo.__tablename}': {e}")
            return 0