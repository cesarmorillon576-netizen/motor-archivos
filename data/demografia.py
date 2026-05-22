from typing import Optional
from sqlmodel import SQLModel, Field


class LenguaIndigena(SQLModel, table=True):
    __tablename__ = "lenguas_indigenas"

    clave_lengua: str = Field(primary_key=True)
    clave_familia: str = Field(index=True)
    familia: Optional[str] = Field(default=None)
    clave_grupo: str = Field(index=True)
    grupo: str
    lengua_indigena: str


class Religion(SQLModel, table=True):
    __tablename__ = "religiones"

    clave_credo: str = Field(primary_key=True)
    credo: str
    clave_grupo: str
    grupo: str
    clave_denominacion: str
    denominacion: str
    clave_religion: str
    religion: str


class Formacion(SQLModel, table=True):
    __tablename__ = "formaciones"

    catalog_key: str = Field(primary_key=True)
    formacion_academica: Optional[str] = Field(default=None)
    agrupacion: str
    grado: str


class Nacionalidad(SQLModel, table=True):
    __tablename__ = "nacionalidades"

    codigo_pais: str = Field(primary_key=True)
    pais: str
    clave_nacionalidad: str
