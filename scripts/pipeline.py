import os
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session
from data.db import engine
from helpers.logger import log
from helpers.parser import obtener_modelo, procesar_archivo
from helpers.sanitizer import normalizar_dataframe, transformar_para_modelo

_BATCH_SIZE = 5_000


def insertar_bd(ruta: str, batch_size: int = _BATCH_SIZE) -> int:
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

    tabla = modelo.__table__
    pk_cols = {c.name for c in tabla.primary_key.columns}
    model_cols = {c.name for c in tabla.columns}

    total = len(df)
    log.info(f"Cargando {total} filas en tabla '{modelo.__tablename__}'...")

    with Session(engine, autoflush=False) as session:
        try:
            insertados = 0
            for i in range(0, total, batch_size):
                lote = df.iloc[i : i + batch_size]
                records = _lote_a_registros(lote, model_cols)
                if not records:
                    continue

                record_cols = set(records[0].keys())
                update_cols = [col for col in record_cols if col not in pk_cols]

                stmt = pg_insert(tabla).values(records)
                if update_cols:
                    stmt = stmt.on_conflict_do_update(
                        index_elements=list(pk_cols),
                        set_={col: stmt.excluded[col] for col in update_cols},
                    )
                else:
                    stmt = stmt.on_conflict_do_nothing(index_elements=list(pk_cols))

                session.execute(stmt)
                session.commit()
                insertados += len(lote)
                log.info(f"lote {i//batch_size + 1} +  {len(lote)} filas")

            log.info(f" {insertados} filas sincronizadas en '{modelo.__tablename__}'")
            return insertados
        except Exception as e:
            session.rollback()
            log.error(f"Error al sincronizar '{modelo.__tablename__}': {e}")
            return 0


def _lote_a_registros(lote: pd.DataFrame, model_cols: set) -> list[dict]:
    df_cols = list(set(lote.columns) & model_cols)
    registros = []
    for _, row in lote.iterrows():
        registro = {}
        for col in df_cols:
            val = row[col]
            try:
                registro[col] = None if pd.isna(val) else val
            except (TypeError, ValueError):
                registro[col] = val
        registros.append(registro)
    return registros
