import os
import pandas as pd
from sqlalchemy import select
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

    pk_presentes = [c for c in pk_cols if c in df.columns]
    if pk_presentes:
        df = df.drop_duplicates(subset=pk_presentes, keep="last").reset_index(drop=True)

    total = len(df)
    log.info(f"Comparando {total} filas contra '{modelo.__tablename__}'...")

    df = _filtrar_cambiados(df, tabla, pk_cols, model_cols)
    cambiados = len(df)

    if cambiados == 0:
        log.info(f"'{modelo.__tablename__}' ya está al día — sin cambios en datos")
        return 0

    if cambiados < total:
        log.info(f"Diff: {cambiados} / {total} filas con cambios reales")
    else:
        log.info(f"Cargando {cambiados} filas nuevas en '{modelo.__tablename__}'")

    with Session(engine, autoflush=False) as session:
        try:
            insertados = 0
            for i in range(0, cambiados, batch_size):
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


def _filtrar_cambiados(
    df: pd.DataFrame,
    tabla,
    pk_cols: set,
    model_cols: set,
) -> pd.DataFrame:
    """
    Devuelve solo las filas que son nuevas o cuyos valores difieren de la BD.
    """
    pk_list = sorted(pk_cols)
    df_cols = [c for c in df.columns if c in model_cols]

    try:
        with engine.connect() as conn:
            df_actual = pd.read_sql(
                select(*[tabla.c[c] for c in df_cols]),
                conn,
            )
    except Exception:
        return df  # tabla todavía no existe → primera carga completa

    if df_actual.empty:
        return df

    h_nuevo = _hash_filas(df, df_cols)
    h_actual = _hash_filas(df_actual, df_cols)

    df_actual = df_actual[pk_list].copy()
    df_actual["_h_db"] = h_actual.values

    df_check = df[pk_list].copy()
    df_check["_h"] = h_nuevo.values

    merged = df_check.merge(df_actual, on=pk_list, how="left")
    mask = merged["_h_db"].isna() | (merged["_h"] != merged["_h_db"])

    return df[mask.values].reset_index(drop=True)


def _hash_filas(df: pd.DataFrame, cols: list) -> pd.Series:
    """
    Hash vectorizado por fila usando pd.util.hash_pandas_object.
    """
    tmp = pd.DataFrame(index=df.index)
    for col in cols:
        # astype(str) antes que fillna: fillna("") revienta en columnas Int64
        # (edad_*_valor), donde '' no es un valor válido para el dtype.
        s = df[col].astype(str)
        s = s.replace({"None": "", "nan": "", "NaN": "", "<NA>": ""})
        s = s.str.replace(r"\.0$", "", regex=True)
        tmp[col] = s
    return pd.util.hash_pandas_object(tmp, index=False)


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
