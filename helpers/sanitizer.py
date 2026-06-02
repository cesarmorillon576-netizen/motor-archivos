import re
import unicodedata
from typing import Optional, Tuple

import pandas as pd

from data.clinico import RestriccionSexo
from .logger import log


_EDAD_RE = re.compile(r"^(\d{1,3})([HDMA])$")

# Valores que significan "sin dato" en los catálogos DGIS
_NULOS = {"", "NO", "NAN", "NA", "NONE", "NULL"}

# Mapa de clave numérica de unidad de edad → letra (catálogo CIE-9-MC DGIS)
# 0 = no aplica, 1 = años, 2 = meses, 3 = días, 4 = horas
_CVE_UNIDAD_EDAD = {"1": "A", "2": "M", "3": "D", "4": "H"}


# ── Parsers atómicos ────────────────────────────────────────────────
def parse_si_no(raw) -> bool:
    """'SI' → True, todo lo demás (incluyendo NaN y 'NO') → False."""
    if raw is None or pd.isna(raw):
        return False
    return str(raw).strip().upper() == "SI"


def parse_sexo_diagnostico(raw) -> str:
    """LSEX del catálogo CIE-10 DGIS: texto 'HOMBRE'/'MUJER'/'NO' → RestriccionSexo."""
    if raw is None or pd.isna(raw):
        return RestriccionSexo.AMBOS.value
    s = str(raw).strip().upper()
    if s == "HOMBRE":
        return RestriccionSexo.HOMBRE.value
    if s == "MUJER":
        return RestriccionSexo.MUJER.value
    return RestriccionSexo.AMBOS.value


def parse_sexo_procedimiento(raw) -> str:
    """SEX_TYPE del catálogo CIE-9-MC DGIS: numérico 0=AMBOS, 1=HOMBRE, 2=MUJER."""
    if raw is None or pd.isna(raw):
        return RestriccionSexo.AMBOS.value
    s = str(raw).strip()
    if s == "1":
        return RestriccionSexo.HOMBRE.value
    if s == "2":
        return RestriccionSexo.MUJER.value
    return RestriccionSexo.AMBOS.value


def parse_edad_concatenada(raw) -> Tuple[Optional[int], Optional[str]]:
    """'028D' → (28, 'D').  'NO'/NaN/'' → (None, None).
    Usado en CIE-10 donde LINF/LSUP vienen en un solo campo."""
    if raw is None or pd.isna(raw):
        return (None, None)
    s = str(raw).strip().upper()
    if s in _NULOS:
        return (None, None)
    m = _EDAD_RE.match(s)
    if not m:
        return (None, None)
    return (int(m.group(1)), m.group(2))


def parse_edad_separada(valor, unidad) -> Tuple[Optional[int], Optional[str]]:
    """Edad donde valor y unidad vienen en columnas distintas (CIE-9-MC).
    La unidad puede ser la clave numérica DGIS (1=A, 2=M, 3=D, 4=H)
    o directamente la letra."""
    if valor is None or pd.isna(valor):
        return (None, None)
    s = str(valor).strip()
    if s in _NULOS or s in {"0", "0.0"}:
        return (None, None)
    try:
        v = int(float(s))
    except ValueError:
        return (None, None)
    if v == 0:
        return (None, None)

    u_raw = str(unidad).strip().upper() if (unidad is not None and not pd.isna(unidad)) else None
    if u_raw:
        u = _CVE_UNIDAD_EDAD.get(u_raw, u_raw)
        if u not in {"H", "D", "M", "A"}:
            u = None
    else:
        u = None
    return (v, u)


# ── Normalización genérica ──────────────────────────────────────────
def _normalizar_columna(col: str) -> str:
    """lowercase, sin tildes, espacios/puntos/guiones → '_', sin guiones dobles."""
    col = unicodedata.normalize("NFKD", col).encode("ASCII", "ignore").decode("ASCII")
    col = col.lower().strip()
    col = re.sub(r"[\s\.\-]+", "_", col)
    col = re.sub(r"_+", "_", col)
    return col


def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        log.warning("Intento de normalizar un dataframe vacío")
        return df

    log.info("Normalizando dataframe...")

    # 1. Nombres de columnas
    df = df.copy()
    df.columns = [_normalizar_columna(c) for c in df.columns]

    # 2. Alias de columnas para mantener compatibilidad
    if "mun_key" in df.columns and "municipio_key" not in df.columns:
        df = df.rename(columns={"mun_key": "municipio_key"})

    # Headers de LOINC que no separan palabras al normalizar → nombre del modelo
    _ALIAS_COLUMNAS = {
        "class": "loinc_class",
        "classtype": "class_type",
        "shortname": "short_name",
        "versionfirstreleased": "version_first_released",
        "versionlastchanged": "version_last_changed",
    }
    for origen, destino in _ALIAS_COLUMNAS.items():
        if origen in df.columns and destino not in df.columns:
            df = df.rename(columns={origen: destino})

    # 3. Normalización de columnas llave (string, sin '.0' residual de lectura como float)
    LLAVES = {
        "catalog_key", "codigo_pais", "clave_familia",
        "efe_key", "municipio_key", "loinc_num", "clave",
    }
    for col in LLAVES & set(df.columns):
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        df.loc[df[col].str.upper().isin(_NULOS), col] = None

    # 4. NaN → None (compatible con INSERT Postgres)
    df = df.where(pd.notna(df), None)

    log.info(f"Columnas normalizadas: {list(df.columns)}")
    return df


# ── Transformaciones específicas por catálogo ───────────────────────
def transformar_diagnostico(df: pd.DataFrame) -> pd.DataFrame:
    """LSEX + LINF/LSUP + flags SI/NO → campos tipados del modelo Diagnostico."""
    df = df.copy()

    edades_min = df["linf"].apply(parse_edad_concatenada)
    edades_max = df["lsup"].apply(parse_edad_concatenada)
    df["edad_min_valor"] = pd.array([e[0] for e in edades_min], dtype=pd.Int64Dtype())
    df["edad_min_unidad"] = [e[1] for e in edades_min]
    df["edad_max_valor"] = pd.array([e[0] for e in edades_max], dtype=pd.Int64Dtype())
    df["edad_max_unidad"] = [e[1] for e in edades_max]

    df["vigente"] = df["valid"].apply(parse_si_no)
    df["valido_consulta_externa"] = df["dia_sis"].apply(parse_si_no)
    df["valido_afeccion_principal"] = df["af_prin"].apply(parse_si_no)
    df["valido_causa_basica_defuncion"] = df["cbd"].apply(parse_si_no)

    df["restriccion_sexo"] = df["lsex"].apply(parse_sexo_diagnostico)

    columnas_modelo = [
        "catalog_key", "nombre", "clave_capitulo", "capitulo",
        "vigente",
        "valido_consulta_externa", "valido_afeccion_principal", "valido_causa_basica_defuncion",
        "restriccion_sexo",
        "edad_min_valor", "edad_min_unidad",
        "edad_max_valor", "edad_max_unidad",
    ]
    return df[columnas_modelo]


def transformar_procedimiento(df: pd.DataFrame) -> pd.DataFrame:
    """SEX_TYPE numérico + pro_edad_ia/pro_cve_edia separados → campos tipados del modelo Procedimiento."""
    df = df.copy()

    # SEX_TYPE: 0=AMBOS, 1=HOMBRE, 2=MUJER (numérico — diferente a CIE-10)
    df["restriccion_sexo"] = df["sex_type"].apply(parse_sexo_procedimiento)

    df["es_principal"] = df["pro_principal"].apply(parse_si_no)

    edades_min = df.apply(
        lambda r: parse_edad_separada(r.get("pro_edad_ia"), r.get("pro_cve_edia")),
        axis=1,
    )
    edades_max = df.apply(
        lambda r: parse_edad_separada(r.get("pro_edad_fa"), r.get("pro_cve_edfa")),
        axis=1,
    )
    df["edad_min_valor"] = pd.array([e[0] for e in edades_min], dtype=pd.Int64Dtype())
    df["edad_min_unidad"] = [e[1] for e in edades_min]
    df["edad_max_valor"] = pd.array([e[0] for e in edades_max], dtype=pd.Int64Dtype())
    df["edad_max_unidad"] = [e[1] for e in edades_max]

    df = df.rename(columns={
        "pro_nombre":        "nombre",
        "pro_seccion":       "seccion",
        "pro_categoria":     "categoria",
        "pro_subcateg":      "subcategoria",
        "pro_grupo_lc":      "grupo_lc",
        "procedimiento_type": "tipo_procedimiento",
    })

    columnas_modelo = [
        "catalog_key", "nombre", "capitulo",
        "seccion", "categoria", "subcategoria", "grupo_lc",
        "tipo_procedimiento", "es_principal",
        "restriccion_sexo",
        "edad_min_valor", "edad_min_unidad",
        "edad_max_valor", "edad_max_unidad",
    ]
    df = df[[c for c in columnas_modelo if c in df.columns]]
    df = df.drop_duplicates(subset=["catalog_key"], keep="first")
    return df


def transformar_localidad(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye el cvegeo INEGI (9 díg: entidad+municipio+localidad) desde las
    claves componentes. La columna CVEGEO del origen pierde el cero inicial en las
    entidades 01–09 (Excel la guarda como número), generando PKs de 8 dígitos que
    no casan con las claves geográficas. Las componentes sí vienen completas."""
    df = df.copy()
    ent = df["efe_key"].fillna("").astype(str).str.strip().str.zfill(2)
    mun = df["municipio_key"].fillna("").astype(str).str.strip().str.zfill(3)
    loc = df["catalog_key"].fillna("").astype(str).str.strip().str.zfill(4)
    df["cvegeo"] = ent + mun + loc
    return df


def transformar_clues(df: pd.DataFrame) -> pd.DataFrame:
    """Catálogo CLUES (DGIS): arma los cvegeo geográficos concatenando
    entidad+municipio+localidad y selecciona solo los campos del modelo.

    El archivo trae las claves por separado (CLAVE DE LA ENTIDAD / DEL MUNICIPIO /
    DE LA LOCALIDAD); aquí se concatenan con relleno de ceros para que coincidan
    con el cvegeo de cat_municipios / cat_localidades."""
    df = df.copy()

    def _clave(serie: pd.Series, ancho: int) -> pd.Series:
        """Limpia, descarta nulos textuales y rellena con ceros a la izquierda."""
        s = serie.fillna("").astype(str).str.strip()
        s = s.mask(s.str.upper().isin(_NULOS), "")
        return s.str.zfill(ancho).where(s != "", None)

    ent = _clave(df["clave_de_la_entidad"], 2)
    mun = _clave(df["clave_del_municipio"], 3)
    loc = _clave(df["clave_de_la_localidad"], 4)

    df["efe_key"] = ent
    df["municipio_cvegeo"] = (ent.fillna("") + mun.fillna("")).where(
        ent.notna() & mun.notna(), None
    )
    df["localidad_cvegeo"] = (ent.fillna("") + mun.fillna("") + loc.fillna("")).where(
        ent.notna() & mun.notna() & loc.notna(), None
    )

    df = df.rename(columns={
        "clave_de_la_institucion": "clave_institucion",
        "clave_de_tipologia":      "clave_tipologia",
        "nombre_de_tipologia":     "nombre_tipologia",
        "estatus_de_operacion":    "estatus_operacion",
        # 'clues', 'nivel_atencion' y 'codigo_postal' ya coinciden tras normalizar
    })

    columnas_modelo = [
        "clues", "clave_institucion", "clave_tipologia", "nombre_tipologia",
        "nivel_atencion", "estatus_operacion",
        "efe_key", "municipio_cvegeo", "localidad_cvegeo", "codigo_postal",
    ]
    df = df[[c for c in columnas_modelo if c in df.columns]]
    df = df.drop_duplicates(subset=["clues"], keep="first")
    return df


# ── Despachador ─────────────────────────────────────────────────────
_TRANSFORMERS = {
    "diagnostico": transformar_diagnostico,
    "procedimiento": transformar_procedimiento,
    "cat_localidades": transformar_localidad,
    "cat_establecimientos_clues": transformar_clues,
}


def transformar_para_modelo(df: pd.DataFrame, tabla: str) -> pd.DataFrame:
    """Aplica la transformación específica del catálogo si existe.
    Si no hay transformer registrado, devuelve el df normalizado sin cambios."""
    fn = _TRANSFORMERS.get(tabla)
    if fn:
        log.info(f"Aplicando transformación específica para '{tabla}'")
        return fn(df)
    return df
