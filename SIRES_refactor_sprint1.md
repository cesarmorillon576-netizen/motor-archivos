# SIRES motor_archivos — Plan de refactor (Sprint 1)

> **Fuente:** logs de ejecución del 21/05/2026 + análisis del catálogo
> CIE-10 + decisiones de arquitectura tomadas en sesión.
>
> **Objetivo:** que la próxima ejecución de `cargar_catalogos.py` cargue
> los 12 catálogos sin error, con modelos consistentes con NOM-024
> Apéndice A.

---

## 1. Diagnóstico del run actual

| # | Catálogo | Estado | Causa raíz |
|---|---|---|---|
| 1 | entidad_federativa | ✅ 35 filas | — |
| 2 | municipio | ✅ 2,478 filas | — |
| 3 | localidades | ⚠️ 296,806 filas en **19 minutos** | `merge()` fila por fila sin batch |
| 4 | procedimiento | ❌ NotNullViolation `pro_subcateg` | Fila `"00"` (encabezado de capítulo) tiene subcategoría vacía; modelo la exige NOT NULL |
| 5 | codigo_postal | ❌ no mapeado | `parser.py` busca substring `"cp"`, el archivo es `codigo_postal_origen.xlsx` |
| 6 | cif | ❌ no mapeado | No existe modelo `CIF` |
| 7 | clues | ❌ no mapeado | No existe modelo `CLUES` (está comentado en `geografia.py`) |
| 8 | lenguas_indigenas | ✅ 95 filas | — |
| 9 | religion | ❌ XLSX corrupto | El archivo descargado tiene XML inválido (probablemente HTML de error en lugar de XLSX) |
| 10 | procedimientos | ❌ misma falla que #4 | URL duplicada en `URLS_CATALOGOS` |
| 11 | formacion_academica | ✅ 7,129 filas | — |
| 12 | nacionalidades | ✅ 172 filas | — |
| 13 | diagnostico | ❌ NotNullViolation `restriccion_sexo`, `edad_minima`, `edad_maxima` | Sanitizer convierte `"NO"` → `None`; modelo exige NOT NULL str |
| 14 | medicamentos | ❌ SSL hostname mismatch | Certificado de `csg.gob.mx` inválido |

**Patrón:** 4 fallos por errores del modelo (4, 9 vs sanitizer, 13), 3 por archivos no mapeados (5, 6, 7), 1 problema de red (14), 1 problema de performance (3), 1 URL duplicada (10).

---

## 2. Cambios por archivo

### 2.1 `data/clinico.py` — REEMPLAZO COMPLETO

Esto refactoriza `Diagnostico`, `Procedimiento` y `LOINC` con enums, edad partida, y nullables correctos.

```python
from enum import Enum
from typing import Optional
from sqlalchemy import CheckConstraint
from sqlmodel import SQLModel, Field


# ── Tipos compartidos ────────────────────────────────────────────────
class RestriccionSexo(str, Enum):
    AMBOS = "AMBOS"
    HOMBRE = "HOMBRE"
    MUJER = "MUJER"


class UnidadEdad(str, Enum):
    HORAS = "H"
    DIAS = "D"
    MESES = "M"
    ANIOS = "A"


# ── Diagnóstico (CIE-10 DGIS) ───────────────────────────────────────
class Diagnostico(SQLModel, table=True):
    """
    CAT_DIAGNOSTICOS, NOM-024-SSA3-2012 Apéndice A.
    Cumple los 4 propósitos del Apéndice: diagnósticos, causas de
    defunción, motivos de consulta, afecciones.
    """
    __tablename__ = "diagnostico"
    __table_args__ = (
        CheckConstraint(
            "restriccion_sexo IN ('AMBOS', 'HOMBRE', 'MUJER')",
            name="ck_diagnostico_restriccion_sexo",
        ),
        CheckConstraint(
            "edad_min_unidad IS NULL OR edad_min_unidad IN ('H','D','M','A')",
            name="ck_diagnostico_edad_min_unidad",
        ),
        CheckConstraint(
            "edad_max_unidad IS NULL OR edad_max_unidad IN ('H','D','M','A')",
            name="ck_diagnostico_edad_max_unidad",
        ),
    )

    # Identificación
    catalog_key: str = Field(primary_key=True, max_length=4)
    nombre: str
    clave_capitulo: str = Field(max_length=5, index=True)
    capitulo: str

    # Vigencia — NOM-024 §6.4.2
    vigente: bool = Field(default=True)

    # Banderas del Apéndice A
    valido_consulta_externa: bool = Field(default=False)        # DIA_SIS
    valido_afeccion_principal: bool = Field(default=False)      # AF_PRIN
    valido_causa_basica_defuncion: bool = Field(default=False)  # CBD

    # Restricciones demográficas
    restriccion_sexo: RestriccionSexo = Field(default=RestriccionSexo.AMBOS)
    edad_min_valor: Optional[int] = Field(default=None)
    edad_min_unidad: Optional[UnidadEdad] = Field(default=None, max_length=1)
    edad_max_valor: Optional[int] = Field(default=None)
    edad_max_unidad: Optional[UnidadEdad] = Field(default=None, max_length=1)


# ── Procedimiento (CIE-9-MC DGIS) ───────────────────────────────────
class Procedimiento(SQLModel, table=True):
    """
    CAT_PROCEDIMIENTOS, NOM-024-SSA3-2012 Apéndice A.
    El catálogo trae edades ya partidas (pro_edad_ia + pro_cve_edia)
    a diferencia de diagnósticos que las trae concatenadas.
    """
    __tablename__ = "procedimiento"
    __table_args__ = (
        CheckConstraint(
            "restriccion_sexo IN ('AMBOS', 'HOMBRE', 'MUJER')",
            name="ck_procedimiento_restriccion_sexo",
        ),
    )

    # Identificación
    catalog_key: str = Field(primary_key=True, max_length=5)
    nombre: str
    capitulo: str

    # Jerarquía oficial — todas nullable porque las filas de
    # encabezado de capítulo no tienen sección/categoría
    seccion: Optional[str] = Field(default=None, index=True)
    categoria: Optional[str] = Field(default=None)
    subcategoria: Optional[str] = Field(default=None)
    grupo_lc: Optional[str] = Field(default=None)

    # Tipo (diagnóstico/terapéutico/quirúrgico/etc.)
    tipo_procedimiento: Optional[str] = Field(default=None)
    es_principal: bool = Field(default=False)

    # Restricciones demográficas
    restriccion_sexo: RestriccionSexo = Field(default=RestriccionSexo.AMBOS)
    edad_min_valor: Optional[int] = Field(default=None)
    edad_min_unidad: Optional[UnidadEdad] = Field(default=None, max_length=1)
    edad_max_valor: Optional[int] = Field(default=None)
    edad_max_unidad: Optional[UnidadEdad] = Field(default=None, max_length=1)


# ── LOINC (Regenstrief) ─────────────────────────────────────────────
class LoincScale(str, Enum):
    QUANTITATIVE = "Qn"
    QUALITATIVE = "Ql"
    ORDINAL = "Ord"
    NOMINAL = "Nom"
    NARRATIVE = "Nar"
    MULTI = "Multi"
    DOCUMENT = "Doc"
    SET = "Set"


class LoincStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    DISCOURAGED = "DISCOURAGED"
    DEPRECATED = "DEPRECATED"


class Loinc(SQLModel, table=True):
    """
    LOINC para órdenes y resultados de laboratorio.
    Licencia: LOINC License (Regenstrief). Conservar copyright notice.
    """
    __tablename__ = "loinc"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE','TRIAL','DISCOURAGED','DEPRECATED')",
            name="ck_loinc_status",
        ),
    )

    loinc_num: str = Field(primary_key=True, max_length=10)
    long_common_name: str
    short_name: Optional[str] = Field(default=None)

    component: str = Field(index=True)
    scale_typ: Optional[LoincScale] = Field(default=None, max_length=8)
    method_typ: Optional[str] = Field(default=None)

    loinc_class: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"name": "class"},
        index=True,
    )
    class_type: Optional[int] = Field(default=None)  # 1=Lab, 2=Clin, 3=Claims, 4=Surveys

    status: LoincStatus = Field(default=LoincStatus.ACTIVE)
    version_first_released: Optional[str] = Field(default=None)
    version_last_changed: Optional[str] = Field(default=None)

    external_copyright_notice: Optional[str] = Field(default=None)
```

**Cambios clave respecto al modelo anterior:**

- `Diagnostico`: edad partida, enums con CHECK constraints, banderas del Apéndice A, defaults para que NULL no rompa el INSERT.
- `Procedimiento`: subcategoría es ahora `Optional`, lo que arregla el error de `"00"`. Edades reciben los campos ya partidos del catálogo (`pro_edad_ia` + `pro_cve_edia`). Agrega `es_principal` y `grupo_lc` que están en el Excel pero antes se ignoraban.
- `Loinc`: renombrado `Class` → `loinc_class` (columna real sigue siendo `class`).

---

### 2.2 `data/constants.py` — quitar URL duplicada

El log muestra que `procedimiento` y `procedimientos` apuntan a la misma URL y se descargan dos veces:

```diff
- "procedimiento": "http://gobi.salud.gob.mx/.../PROCEDIMIENTO_202402.xlsx?v=2024.02.21",
- "procedimientos": "http://gobi.salud.gob.mx/.../PROCEDIMIENTO_202402.xlsx?v=2024.02.21",
+ "procedimiento": "http://gobi.salud.gob.mx/.../PROCEDIMIENTO_202402.xlsx?v=2024.02.21",
```

Mantén solo `procedimiento` (singular) porque encaja con `MAPEO_MODELOS` actual.

---

### 2.3 `data/__init__.py` — exportar enums

Para que `helpers/sanitizer.py` los pueda importar:

```python
# data/__init__.py
from .clinico import (
    Diagnostico, Procedimiento, Loinc,
    RestriccionSexo, UnidadEdad, LoincScale, LoincStatus,
)
from .demografia import LenguaIndigena, Religion, Formacion, Nacionalidad
from .geografia import EntidadFederativa, Municipio, Localidad, CodigoPostal
from .insumos import Medicamento
from .db import engine, iniciar_bd, get_session
from .constants import URLS_CATALOGOS
```

Renombra `LOINC` → `Loinc` (Pascal case Python). Si NestJS ya consume el nombre `LOINC`, mantenlo, pero internamente la convención es Pascal.

---

### 2.4 `helpers/parser.py` — mapeo robusto

El mapeo por substring falla en `codigo_postal_origen.xlsx` porque busca `"cp"` (no aparece como palabra) en lugar de la palabra completa. Solución:

```python
import os
import re
import pandas as pd
import data
from .logger import log


# Patrones de mapeo: regex que matchean el nombre del archivo
# El orden importa: el primero que matchea gana.
MAPEO_MODELOS = [
    (r"diagnostico",          data.Diagnostico),
    (r"procedimiento",        data.Procedimiento),
    (r"loinc",                data.Loinc),
    (r"lengua",               data.LenguaIndigena),
    (r"religion",             data.Religion),
    (r"formacion",            data.Formacion),
    (r"nacionalidad",         data.Nacionalidad),
    (r"entidad",              data.EntidadFederativa),
    (r"municipio",            data.Municipio),
    (r"localidad",            data.Localidad),
    (r"codigo[_ ]?postal|^cp_", data.CodigoPostal),  # ← FIX #5
    (r"medicamento",          data.Medicamento),
    # CLUES y CIF pendientes — ver sección 3
]


def obtener_modelo(ruta_archivo: str):
    nombre = os.path.basename(ruta_archivo).lower()
    for patron, modelo in MAPEO_MODELOS:
        if re.search(patron, nombre):
            log.info(f"Archivo {ruta_archivo} corresponde a {modelo.__tablename__}")
            return modelo
    log.warning(f"Archivo {ruta_archivo} no corresponde a ningún modelo")
    return None


def procesar_archivo(ruta_archivo: str) -> pd.DataFrame:
    if not os.path.exists(ruta_archivo):
        log.error(f"Archivo {ruta_archivo} no existe")
        return pd.DataFrame()

    extension = os.path.splitext(ruta_archivo)[1].lower()
    log.info(f"Leyendo: {ruta_archivo}")

    try:
        # Leer todo como string evita inferencias erróneas
        # (CLAVE_PROGRAMA_SIS como float con NaN, edades como int, etc.)
        if extension in (".xlsx", ".xlsm"):
            df = pd.read_excel(ruta_archivo, engine="openpyxl", dtype=str)
        elif extension == ".xls":
            df = pd.read_excel(ruta_archivo, engine="xlrd", dtype=str)
        elif extension == ".csv":
            try:
                df = pd.read_csv(ruta_archivo, encoding="utf-8", dtype=str)
            except UnicodeDecodeError:
                log.warning(f"UTF-8 falló en {ruta_archivo}, reintentando ISO-8859-1")
                df = pd.read_csv(ruta_archivo, encoding="ISO-8859-1", dtype=str)
        else:
            log.error(f"Extensión no soportada: {extension}")
            return pd.DataFrame()

        df.dropna(how="all", inplace=True)
        return df

    except Exception as e:
        # XLSX corrupto (caso religión) cae aquí
        log.error(f"Error al procesar {ruta_archivo}: {e}")
        return pd.DataFrame()
```

**Cambios:**

1. `MAPEO_MODELOS` cambia de `dict` a `list` de tuplas porque el orden importa cuando hay regex que solapan (ej. `"procedimiento"` matchearía con `"medicamento"` si fueran al revés en un dict no-ordenado). En Python 3.7+ los dicts mantienen orden, pero la intención es más clara con lista.
2. Regex en lugar de `in`: `codigo[_ ]?postal` matchea `codigo_postal`, `codigopostal`, `codigo postal`.
3. `dtype=str` al leer evita que pandas infiera tipos mal.

---

### 2.5 `helpers/sanitizer.py` — parsers tipados + transformaciones por catálogo

El sanitizer actual hace transformaciones genéricas que mezclan dos cosas:
limpieza universal y parches específicos de catálogo. Conviene separarlas.

**Estructura propuesta:**

```python
# helpers/sanitizer.py
import re
import unicodedata
from typing import Optional, Tuple
import pandas as pd
from data.clinico import RestriccionSexo, UnidadEdad
from .logger import log


# ── Parsers atómicos ────────────────────────────────────────────────
_EDAD_RE = re.compile(r"^(\d{1,3})([HDMA])$")
_NULOS = {"", "NO", "NAN", "NA", "NONE", "NULL"}


def parse_si_no(raw) -> bool:
    """SI → True, todo lo demás → False."""
    if raw is None or pd.isna(raw):
        return False
    return str(raw).strip().upper() == "SI"


def parse_sexo(raw) -> str:
    """LSEX del catálogo DGIS → valor de RestriccionSexo."""
    if raw is None or pd.isna(raw):
        return RestriccionSexo.AMBOS.value
    s = str(raw).strip().upper()
    if s == "HOMBRE":
        return RestriccionSexo.HOMBRE.value
    if s == "MUJER":
        return RestriccionSexo.MUJER.value
    return RestriccionSexo.AMBOS.value


def parse_edad_concatenada(raw) -> Tuple[Optional[int], Optional[str]]:
    """'028D' → (28, 'D'). 'NO'/NaN/'' → (None, None). Para LINF/LSUP de CIE-10."""
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
    """Para procedimientos donde pro_edad_ia y pro_cve_edia vienen separados."""
    if valor is None or pd.isna(valor):
        return (None, None)
    s = str(valor).strip()
    if s in _NULOS or s in {"0", "0.0"}:
        return (None, None)
    try:
        v = int(float(s))
    except ValueError:
        return (None, None)
    u = str(unidad).strip().upper() if unidad and not pd.isna(unidad) else None
    if u not in {"H", "D", "M", "A"}:
        u = None
    return (v, u)


# ── Normalización genérica ──────────────────────────────────────────
def _normalizar_columna(col: str) -> str:
    """lowercase, sin tildes, espacios y '.' → '_'."""
    col = unicodedata.normalize("NFKD", col).encode("ASCII", "ignore").decode("ASCII")
    col = col.lower().strip()
    col = re.sub(r"[\s\.\-]+", "_", col)
    col = re.sub(r"_+", "_", col)
    return col


def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza genérica que aplica a todos los catálogos."""
    log.info("Normalizando dataframe...")

    # 1. Nombres de columnas
    df.columns = [_normalizar_columna(c) for c in df.columns]

    # 2. Alias conocidos (mantener compatibilidad)
    if "mun_key" in df.columns and "municipio_key" not in df.columns:
        df = df.rename(columns={"mun_key": "municipio_key"})

    # 3. Normalización de llaves (string, sin '.0' de floats)
    LLAVES = {"catalog_key", "codigo_pais", "clave_familia", "efe_key",
              "municipio_key", "loinc_num", "clave"}
    for col in LLAVES & set(df.columns):
        df[col] = df[col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        df.loc[df[col].isin(_NULOS), col] = None

    # 4. NaN → None (Postgres-friendly)
    df = df.where(pd.notna(df), None)

    log.info(f"Columnas normalizadas: {list(df.columns)}")
    return df


# ── Transformaciones específicas por catálogo ───────────────────────
def transformar_diagnostico(df: pd.DataFrame) -> pd.DataFrame:
    """LSEX, LINF, LSUP → campos tipados del modelo Diagnostico."""
    df = df.copy()

    # Partir edades
    edades_min = df["linf"].apply(parse_edad_concatenada)
    edades_max = df["lsup"].apply(parse_edad_concatenada)
    df["edad_min_valor"] = [e[0] for e in edades_min]
    df["edad_min_unidad"] = [e[1] for e in edades_min]
    df["edad_max_valor"] = [e[0] for e in edades_max]
    df["edad_max_unidad"] = [e[1] for e in edades_max]

    # Mapeo SI/NO → bool
    df["vigente"] = df["valid"].apply(parse_si_no)
    df["valido_consulta_externa"] = df["dia_sis"].apply(parse_si_no)
    df["valido_afeccion_principal"] = df["af_prin"].apply(parse_si_no)
    df["valido_causa_basica_defuncion"] = df["cbd"].apply(parse_si_no)

    # Sexo
    df["restriccion_sexo"] = df["lsex"].apply(parse_sexo)

    # Conservar solo las columnas que el modelo espera
    columnas_modelo = [
        "catalog_key", "nombre", "clave_capitulo", "capitulo", "vigente",
        "valido_consulta_externa", "valido_afeccion_principal",
        "valido_causa_basica_defuncion", "restriccion_sexo",
        "edad_min_valor", "edad_min_unidad",
        "edad_max_valor", "edad_max_unidad",
    ]
    return df[columnas_modelo]


def transformar_procedimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Adapta el catálogo CIE-9-MC al modelo Procedimiento."""
    df = df.copy()

    edades_min = df.apply(
        lambda r: parse_edad_separada(r.get("pro_edad_ia"), r.get("pro_cve_edia")),
        axis=1,
    )
    edades_max = df.apply(
        lambda r: parse_edad_separada(r.get("pro_edad_fa"), r.get("pro_cve_edfa")),
        axis=1,
    )
    df["edad_min_valor"] = [e[0] for e in edades_min]
    df["edad_min_unidad"] = [e[1] for e in edades_min]
    df["edad_max_valor"] = [e[0] for e in edades_max]
    df["edad_max_unidad"] = [e[1] for e in edades_max]

    df["restriccion_sexo"] = df["sex_type"].apply(parse_sexo)
    df["es_principal"] = df["pro_principal"].apply(parse_si_no)

    df = df.rename(columns={
        "pro_nombre": "nombre",
        "pro_seccion": "seccion",
        "pro_categoria": "categoria",
        "pro_subcateg": "subcategoria",
        "pro_grupo_lc": "grupo_lc",
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
    return df[[c for c in columnas_modelo if c in df.columns]]


# ── Despachador ─────────────────────────────────────────────────────
TRANSFORMERS = {
    "diagnostico": transformar_diagnostico,
    "procedimiento": transformar_procedimiento,
    # añadir loinc, medicamento, etc. cuando se necesiten
}


def transformar_para_modelo(df: pd.DataFrame, tabla: str) -> pd.DataFrame:
    """Aplica transformación específica si existe, si no devuelve el df normalizado."""
    fn = TRANSFORMERS.get(tabla)
    if fn:
        log.info(f"Aplicando transformación específica para '{tabla}'")
        return fn(df)
    return df
```

**Lo que se elimina del sanitizer actual:**

- El parche de `procategoria = 'SIN CATEGORIA'`. Estos campos genéricos contaminaban catálogos que no los necesitan. Si algún catálogo específico los requiere de verdad, va en su transformer.
- El parche de `nivel = 0`. Igual razón.
- El parche de `abreviatura = 'N/A'`. Solo aplica a `EntidadFederativa`; va en un futuro `transformar_entidad` si hace falta.

---

### 2.6 `helpers/extractor.py` — fallback SSL

Para `csg.gob.mx` (compendio de medicamentos). El certificado tiene hostname mismatch pero el archivo es público y legítimo. Una solución sin desactivar SSL globalmente:

```python
import os
import zipfile
import requests
import urllib3
from .logger import log


# Dominios donde el SSL falla pero el archivo es legítimo y público.
# Documentado conscientemente; no expandir esta lista sin justificación.
DOMINIOS_SSL_RELAJADO = {
    "csg.gob.mx",  # Compendio Nacional de Insumos para la Salud
}


def descargar_archivo(url: str, destino: str) -> bool:
    try:
        log.info(f"Descargando archivo desde {url}")

        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        verify_ssl = host not in DOMINIOS_SSL_RELAJADO

        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            log.warning(f"SSL relajado para {host} (dominio whitelisted)")

        response = requests.get(url, timeout=30, stream=True, verify=verify_ssl)
        response.raise_for_status()

        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            for bloque in response.iter_content(chunk_size=8192):
                f.write(bloque)
        log.info(f"Archivo guardado en {destino}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"Error de red al descargar desde {url}: {e}")
        return False
    except Exception as e:
        log.error(f"Error al guardar {destino}: {e}")
        return False


def extraer_zip(ruta_zip: str, destino: str) -> bool:
    try:
        if not os.path.exists(ruta_zip):
            log.error(f"El archivo ZIP {ruta_zip} no existe")
            return False
        log.info(f"Extrayendo ZIP desde {ruta_zip}")
        os.makedirs(destino, exist_ok=True)
        with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
            zip_ref.extractall(destino)
        log.info(f"ZIP extraído en {destino}")
        return True
    except zipfile.BadZipFile as e:
        log.error(f"{ruta_zip} no es un ZIP válido: {e}")
        return False
    except Exception as e:
        log.error(f"Error al extraer {ruta_zip}: {e}")
        return False
```

> **Nota de seguridad:** el bypass SSL está limitado por whitelist explícita
> a `csg.gob.mx`. No se relaja globalmente. Cuando CSG arregle el certificado,
> quitar el dominio del set.

---

### 2.7 `scripts/cargar_catalogos.py` — batch insert + transformaciones

```python
from sqlmodel import Session
from data.db import engine, iniciar_bd
from data.constants import URLS_CATALOGOS
from helpers import (
    log, descargar_archivo, extraer_zip,
    escanear_directorio, obtener_modelo, procesar_archivo,
    normalizar_dataframe,
)
from helpers.sanitizer import transformar_para_modelo
import os


# Orden de FK: los padres primero
ORDEN_PRIORIDAD = [
    "entidad_federativa", "municipio", "localidades",
    # el resto en cualquier orden
]


def descargar_catalogos(destino="descargas"):
    for clave, url in URLS_CATALOGOS.items():
        if clave == "loinc":
            log.info("LOINC omitido (descarga manual desde loinc.org)")
            continue

        ext = os.path.splitext(url.split("?")[0])[1].lower() or ".xlsx"
        ruta = os.path.join(destino, f"{clave}_origen{ext}")
        descargar_archivo(url, ruta)

        if ext == ".zip":
            extraer_zip(ruta, os.path.join(destino, f"{clave}_extraido"))


def cargar_archivo(ruta: str, batch_size: int = 5000) -> int:
    modelo = obtener_modelo(ruta)
    if not modelo:
        log.warning(f"Saltando {ruta}: no mapeado")
        return 0

    df = procesar_archivo(ruta)
    if df.empty:
        log.warning(f"Saltando {ruta}: DataFrame vacío")
        return 0

    df = normalizar_dataframe(df)
    df = transformar_para_modelo(df, modelo.__tablename__)

    log.info(f"Cargando {len(df)} filas en '{modelo.__tablename__}'")

    with Session(engine, autoflush=False) as session:
        try:
            for i in range(0, len(df), batch_size):
                lote = df.iloc[i:i + batch_size]
                for _, fila in lote.iterrows():
                    # Filtrar None → no asignar (deja que el default actúe)
                    datos = {k: v for k, v in fila.to_dict().items() if v is not None}
                    session.merge(modelo(**datos))
                session.commit()
                log.info(f"  batch {i//batch_size + 1}: +{len(lote)} filas")
            log.info(f"✓ Sincronizadas {len(df)} filas en '{modelo.__tablename__}'")
            return len(df)
        except Exception as e:
            session.rollback()
            log.error(f"Error en '{modelo.__tablename__}': {e}")
            return 0


def orquestador(carpeta="descargas"):
    iniciar_bd()  # ⚠ TEMPORAL — eliminar cuando NestJS gestione migraciones
    descargar_catalogos(carpeta)

    arbol = escanear_directorio(carpeta)
    archivos = arbol["excel"] + arbol["csv"]

    def prioridad(ruta):
        nombre = os.path.basename(ruta).lower()
        for i, clave in enumerate(ORDEN_PRIORIDAD):
            if clave in nombre:
                return i
        return len(ORDEN_PRIORIDAD)

    archivos.sort(key=prioridad)

    for archivo in archivos:
        log.info(f"Procesando: {os.path.basename(archivo)}")
        cargar_archivo(archivo)
        log.info("=" * 50)


if __name__ == "__main__":
    orquestador()
```

**Cambios clave:**

1. `Session(engine, autoflush=False)`: previene que SQLAlchemy haga flush prematuro en cada merge. Esto **soluciona el `Query-invoked autoflush`** que aparece en los errores actuales.
2. `commit()` por batch de 5000 en lugar de uno solo al final. Las 296k localidades pasarán de 19 min a unos pocos minutos (probable 2-3× a 5× más rápido).
3. `datos = {k: v for k, v in fila.to_dict().items() if v is not None}`: para que cuando el sanitizer mande `None`, el modelo use su `default` declarado en lugar de forzar NULL en la columna. Esto **soluciona los NotNullViolation** de diagnóstico y procedimiento.
4. Llamada a `transformar_para_modelo(df, modelo.__tablename__)` después de la normalización genérica.

---

## 3. Pendientes que necesitan decisión

### 3.1 CLUES (catálogo de establecimientos de salud)

**Estado:** modelo comentado en `geografia.py`. Es obligatorio por NOM-024 (Apéndice A `CAT_CLUES`) y por §6.5.

**Bloqueante:** necesitamos analizar el archivo `clues_origen.xlsx` real para decidir qué campos modelar. La clave CLUES tiene estructura significativa:

```
[2 letras][3 letras][3 letras][2 letras][3 dígitos]
 entidad  institución  jurisdicción  tipo  consecutivo
```

**Acción:** abrir `descargas/clues_origen.xlsx` en la próxima sesión y proponer el modelo.

### 3.2 CIF (Clasificación Internacional del Funcionamiento)

**Estado:** descargado pero sin modelo. Apéndice A lo nombra (`CAT_CIF`) para "registrar información sobre niveles de funcionamiento y estados de salud".

**Acción:** decidir si entra en este sprint o en el siguiente. No es crítico para el MVP de captura clínica básica.

### 3.3 Catálogo de religiones — archivo corrupto

**Causa probable:** el servidor `gobi.salud.gob.mx` está devolviendo HTML de error (404, 500, etc.) en lugar del XLSX. El descargador guarda los bytes sin validar y openpyxl falla al abrir.

**Mitigaciones a evaluar:**

1. Validar `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` antes de guardar.
2. Verificar el "magic number" (`PK\x03\x04` para zip-based, que incluye XLSX) tras descarga.
3. Re-intentar con backoff si la primera descarga falla.

**Acción:** agregar validación post-descarga en `extractor.py`. Lo puedo hacer en el siguiente paso.

### 3.4 Performance de localidades (296k filas)

El batch de 5000 + autoflush=False debería reducir significativamente los 19 min. Si aún es lento, alternativas:

- **`bulk_insert_mappings`**: 10-50× más rápido que merge pero no hace upsert. Solo viable para la primera carga o si truncamos primero.
- **`INSERT ... ON CONFLICT DO UPDATE`**: PostgreSQL nativo. Requiere SQL directo o `psycopg2.extras.execute_values`.
- **`COPY`**: el más rápido para cargas masivas. Requiere preparar CSV en memoria.

**Acción:** medir el nuevo tiempo después del refactor; si sigue siendo inaceptable, escalar a `ON CONFLICT`.

### 3.5 LOINC

Sigue requiriendo descarga manual desde loinc.org (registro obligatorio). El loader debe esperar el archivo en `descargas/Loinc_*.csv` y procesarlo si está presente.

---

## 4. Orden recomendado de aplicación

1. **`data/clinico.py`** (refactor completo) — necesario para los demás.
2. **`data/__init__.py`** — exportar enums.
3. **`helpers/parser.py`** — para que `codigo_postal`
 sea detectado.
4. **`helpers/sanitizer.py`** — los parsers tipados.
5. **`scripts/cargar_catalogos.py`** — batch insert + filtrado de `None`.
6. **`helpers/extractor.py`** — fallback SSL.
7. **`data/constants.py`** — quitar URL duplicada.

Después de aplicar 1-7, el `DROP TABLE` manual + nuevo `iniciar_bd()` es necesario porque las columnas cambiaron. En PostgreSQL:

```sql
DROP TABLE IF EXISTS diagnostico, procedimiento, loinc CASCADE;
```

Y luego correr `python scripts/cargar_catalogos.py` debería procesar todos los catálogos sin las fallas del run anterior.

---

## 5. Lo que NO se está atacando en este sprint

- **CLUES, CIF, código postal (modelo):** pendientes de análisis del Excel.
- **Religión (archivo corrupto):** pendiente de validación post-descarga.
- **Medicamento PK natural:** cambio de `id` autoincrement a `clave: str` como PK. Es necesario pero requiere coordinar con el equipo de NestJS si ya hay código consumiéndolo.
- **Migración a Alembic:** `iniciar_bd()` seguirá usándose en prototipado.
- **Adaptadores FHIR:** se atacan cuando los modelos estén estables.
