from typing import Optional
from sqlmodel import SQLModel, Field
from typing import Any

class EntidadFederativa(SQLModel, table=True):
    __tablename__: Any = "cat_entidades_federativas"

    catalog_key: str = Field(primary_key=True)
    entidad_federativa: str
    abreviatura: Optional[str] = Field(default=None)


class Municipio(SQLModel, table=True):
    __tablename__: Any = "cat_municipios"

    cvegeo: str = Field(primary_key=True)
    catalog_key: str = Field(index=True)
    municipio: str
    efe_key: str = Field(index=True)


class Localidad(SQLModel, table=True):
    __tablename__: Any = "cat_localidades"

    cvegeo: str = Field(primary_key=True)
    catalog_key: str = Field(index=True)
    localidad: str
    efe_key: str = Field(index=True)
    municipio_key: str = Field(index=True)


class CodigoPostal(SQLModel, table=True):
    __tablename__: Any = "codigos_postales"

    c_estado: str = Field(primary_key=True)
    c_mnpio: str = Field(primary_key=True)
    id_asenta_cpcons: str = Field(primary_key=True)

    d_codigo: str = Field(index=True)       
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


class CLUES(SQLModel, table=True):
    __tablename__: Any = "cat_establecimientos_clues"

    clues: str = Field(primary_key=True, max_length=13)
    clave_institucion: str = Field(index=True)
    clave_tipologia: Optional[str] = Field(default=None, index=True)
    nombre_tipologia: Optional[str] = Field(default=None)
    nivel_atencion: Optional[str] = Field(default=None)
    estatus_operacion: str = Field(index=True)

    # Claves geográficas en formato cvegeo (entidad+municipio[+localidad]),
    # reconstruidas en transformar_clues para casar con cat_municipios/cat_localidades.
    efe_key: str = Field(index=True)
    municipio_cvegeo: Optional[str] = Field(default=None, index=True)
    localidad_cvegeo: Optional[str] = Field(default=None, index=True)

    codigo_postal: Optional[str] = Field(default=None, index=True)
