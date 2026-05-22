from typing import Optional
from sqlmodel import SQLModel, Field


class EntidadFederativa(SQLModel, table=True):
    __tablename__ = "cat_entidades_federativas"

    catalog_key: str = Field(primary_key=True)
    entidad_federativa: str
    # Nullable: algunas entidades especiales (ej. catalog_key='88') no tienen abreviatura en el fuente.
    abreviatura: Optional[str] = Field(default=None)


class Municipio(SQLModel, table=True):
    __tablename__ = "cat_municipios"

    # cvegeo es el código geográfico único nacional (efe_key + catalog_key).
    # catalog_key solo es único dentro de una misma entidad federativa.
    cvegeo: str = Field(primary_key=True)
    catalog_key: str = Field(index=True)
    municipio: str
    efe_key: str = Field(index=True)


class Localidad(SQLModel, table=True):
    __tablename__ = "cat_localidades"

    # cvegeo es el código geográfico único nacional (296,806 valores distintos).
    # catalog_key se repite entre municipios — no es PK global.
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
# Ver SIRES_refactor_sprint1.md sección 3.1.
