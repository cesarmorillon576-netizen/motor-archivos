import pandas as pd
import unicodedata
from .logger import log

def limpiar_nombre_columna(columna: str) -> str:
    col = str(columna).strip().lower()

    col = col.replace(" ", "_").replace("-", "_")

    col = "".join(
        c for c in unicodedata.normalize('NFD', col)
        if unicodedata.category(c) != 'Mn'
    )

    return col

def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        log.warning(f"Intento de normalizar un dataframe vacio.")
        return df

    log.info("Limpiando columnas...")

    df.columns = [limpiar_nombre_columna(col) for col in df.columns]
    
    df = df.where(pd.notnull(df), None)

    log.info(f"Dataframe normalizado. Columnas resultantes: {list(df.columns)}")
    return df
