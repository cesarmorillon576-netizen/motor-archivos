from enum import Enum
from typing import Optional
from sqlalchemy import CheckConstraint
from sqlmodel import SQLModel, Field
from typing import Any

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
    __tablename__: Any = "diagnostico"
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

    catalog_key: str = Field(primary_key=True)
    nombre: str
    clave_capitulo: str = Field(index=True)
    capitulo: str

    # NOM-024 §6.4.2
    vigente: bool = Field(default=True)

    # Banderas Apéndice A
    valido_consulta_externa: bool = Field(default=False)
    valido_afeccion_principal: bool = Field(default=False)
    valido_causa_basica_defuncion: bool = Field(default=False)

    restriccion_sexo: str = Field(default=RestriccionSexo.AMBOS.value)
    edad_min_valor: Optional[int] = Field(default=None)
    edad_min_unidad: Optional[str] = Field(default=None)
    edad_max_valor: Optional[int] = Field(default=None)
    edad_max_unidad: Optional[str] = Field(default=None)


# ── Procedimiento (CIE-9-MC DGIS) ───────────────────────────────────
class Procedimiento(SQLModel, table=True):
    __tablename__: Any = "procedimiento"
    __table_args__ = (
        CheckConstraint(
            "restriccion_sexo IN ('AMBOS', 'HOMBRE', 'MUJER')",
            name="ck_procedimiento_restriccion_sexo",
        ),
    )

    catalog_key: str = Field(primary_key=True)
    nombre: str
    capitulo: str

    # Jerarquía del catálogo — nullable porque las filas de encabezado de capítulo no tienen sección/categoría
    seccion: Optional[str] = Field(default=None, index=True)
    categoria: Optional[str] = Field(default=None)
    subcategoria: Optional[str] = Field(default=None)
    grupo_lc: Optional[str] = Field(default=None)

    tipo_procedimiento: Optional[str] = Field(default=None)
    es_principal: bool = Field(default=False)

    restriccion_sexo: str = Field(default=RestriccionSexo.AMBOS.value)
    edad_min_valor: Optional[int] = Field(default=None)
    edad_min_unidad: Optional[str] = Field(default=None)
    edad_max_valor: Optional[int] = Field(default=None)
    edad_max_unidad: Optional[str] = Field(default=None)


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
    __tablename__: Any = "loinc"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE','TRIAL','DISCOURAGED','DEPRECATED')",
            name="ck_loinc_status",
        ),
    )

    loinc_num: str = Field(primary_key=True)
    long_common_name: str
    short_name: Optional[str] = Field(default=None)

    component: str = Field(index=True)
    scale_typ: Optional[str] = Field(default=None)
    method_typ: Optional[str] = Field(default=None)

    loinc_class: Optional[str] = Field(default=None, index=True)
    class_type: Optional[str] = Field(default=None)

    status: str = Field(default=LoincStatus.ACTIVE.value)
    version_first_released: Optional[str] = Field(default=None)
    version_last_changed: Optional[str] = Field(default=None)
    external_copyright_notice: Optional[str] = Field(default=None)


# TODO: CIF pendiente de análisis del catálogo origen.
# class CIF(SQLModel, table=True):
#     __tablename__ = "cif"
#
#     cif_num: str = Field(primary_key=True)
#     nombre: str
#     descripcion: Optional[str] = Field(default=None)
