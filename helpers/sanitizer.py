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
    
    if 'mun_key' in df.columns and 'municipio_key' not in df.columns:
        df['municipio_key'] = df['mun_key']

    columnas_llave = ['catalog_key', 'codigo_pais', 'clave_familia', 'efe_key', 'mun_key', 'municipio_key']
    for col in columnas_llave:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    if 'pro_categoria' in df.columns:
        df['procategoria'] = df['pro_categoria'].fillna('SIN CATEGORIA')
    elif 'procategoria' in df.columns:
        df['procategoria'] = df['procategoria'].fillna('SIN CATEGORIA')
    else:
        df['procategoria'] = 'SIN CATEGORIA'

    if 'nivel' not in df.columns:
        df['nivel'] = 0
    else:
        df['nivel'] = df['nivel'].fillna(0).astype(int)
        
    if 'abreviatura' not in df.columns:
        df['abreviatura'] = 'N/A'
    else:
        df['abreviatura'] = df['abreviatura'].fillna('N/A')

    df = df.where(pd.notnull(df), None)

    log.info(f"Dataframe normalizado. Columnas resultantes: {list(df.columns)}")
    return df