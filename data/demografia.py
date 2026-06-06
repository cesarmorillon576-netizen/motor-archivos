from typing import Optional
from sqlmodel import SQLModel, Field
from typing import Any

class LenguaIndigena(SQLModel, table=True):
    __tablename__: Any = "lenguas_indigenas"

    clave_lengua: str = Field(primary_key=True)
    clave_familia: str = Field(index=True)
    familia: Optional[str] = Field(default=None)
    clave_grupo: str = Field(index=True)
    grupo: str
    lengua_indigena: str


class Religion(SQLModel, table=True):
    __tablename__: Any = "religiones"

    clave_religion: str = Field(primary_key=True)
    religion: Optional[str] = Field(default=None)
    clave_credo: Optional[str] = Field(default=None, index=True)
    credo: Optional[str] = Field(default=None)
    clave_grupo: Optional[str] = Field(default=None, index=True)
    grupo: Optional[str] = Field(default=None)
    clave_denominacion: Optional[str] = Field(default=None)
    denominacion: Optional[str] = Field(default=None)


class Formacion(SQLModel, table=True):
    __tablename__: Any = "formaciones"

    catalog_key: str = Field(primary_key=True)
    formacion_academica: Optional[str] = Field(default=None)
    agrupacion: str
    grado: str


class Nacionalidad(SQLModel, table=True):
    __tablename__: Any = "nacionalidades"

    codigo_pais: str = Field(primary_key=True)
    pais: str
    clave_nacionalidad: str
