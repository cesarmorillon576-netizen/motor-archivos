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

    catalog_key: str = Field(primary_key=True)
    codigo_postal: str


# TODO: Modelo CLUES pendiente de análisis del esquema real (68 columnas).
