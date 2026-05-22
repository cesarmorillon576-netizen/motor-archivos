from typing import Optional
from sqlmodel import SQLModel, Field


class EntidadFederativa(SQLModel, table=True):
    __tablename__ = "cat_entidades_federativas"

    catalog_key: str = Field(primary_key=True)
    entidad_federativa: str
    abreviatura: Optional[str] = Field(default=None)


class Municipio(SQLModel, table=True):
    __tablename__ = "cat_municipios"

    cvegeo: str = Field(primary_key=True)
    catalog_key: str = Field(index=True)
    municipio: str
    efe_key: str = Field(index=True)


class Localidad(SQLModel, table=True):
    __tablename__ = "cat_localidades"

    cvegeo: str = Field(primary_key=True)
    catalog_key: str = Field(index=True)
    localidad: str
    efe_key: str = Field(index=True)
    municipio_key: str = Field(index=True)


class CodigoPostal(SQLModel, table=True):
    __tablename__ = "codigos_postales"

    # PK compuesta: estado + municipio + ID secuencial del asentamiento
    c_estado: str = Field(primary_key=True)
    c_mnpio: str = Field(primary_key=True)
    id_asenta_cpcons: str = Field(primary_key=True)

    d_codigo: str = Field(index=True)        # código postal (puede ser compartido)
    d_asenta: Optional[str] = Field(default=None)
    d_tipo_asenta: Optional[str] = Field(default=None)
    d_mnpio: Optional[str] = Field(default=None)
    d_estado: Optional[str] = Field(default=None)
    d_ciudad: Optional[str] = Field(default=None)
    d_cp: Optional[str] = Field(default=None)
    c_oficina: Optional[str] = Field(default=None)
    c_cp: Optional[str] = Field(default=None)
    c_tipo_asenta: Optional[str] = Field(default=None)
    d_zona: Optional[str] = Field(default=None)
    c_cve_ciudad: Optional[str] = Field(default=None)


# TODO: Modelo CLUES pendiente de análisis del esquema real (68 columnas).
